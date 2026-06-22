"""Post-demo intelligence orchestrator."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.db.models import DemoSession, Product
from live_demo_api.errors import ForbiddenError, NotFoundError
from live_demo_api.events.event_bus import EventBus
from live_demo_api.post_demo.crm.crm_export_policy import can_export_crm
from live_demo_api.post_demo.crm.crm_export_service import CrmExportService
from live_demo_api.post_demo.evidence.evidence_loader import EvidenceLoader
from live_demo_api.post_demo.evidence.evidence_types import EvidenceLoadRequest
from live_demo_api.post_demo.features.feature_shown_tracker import FeatureShownTracker
from live_demo_api.post_demo.insights.lead_insight_extractor import LeadInsightExtractor
from live_demo_api.post_demo.post_demo_job_types import PostDemoJobEnvelope
from live_demo_api.post_demo.repositories.features_shown import FeatureShownRepository
from live_demo_api.post_demo.repositories.lead_insights import LeadInsightPostDemoRepository
from live_demo_api.post_demo.repositories.lead_summaries import LeadSummaryPostDemoRepository
from live_demo_api.post_demo.repositories.post_demo_jobs import PostDemoJobRepository
from live_demo_api.post_demo.summaries.lead_summary_generator import LeadSummaryGenerator
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.audit_service import publish_event
from live_demo_backend_common.observability import metric_names, span_names
from live_demo_backend_common.observability.metrics import get_global_registry
from live_demo_backend_common.observability.trace_context import TraceContext
from live_demo_backend_common.observability.tracing import start_span


class PostDemoOrchestrator:
    async def run_full(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        request_context: RequestContext,
        *,
        session_id: UUID,
        export_crm: bool,
        crm_provider: str,
    ) -> dict[str, Any]:
        started_ns = time.perf_counter_ns()
        settings = get_settings()
        trace_id = request_context.trace_id or request_context.request_id
        trace_context = (
            TraceContext(trace_id=trace_id, span_id=session_id.hex[:16])
            if len(trace_id) == 32
            else TraceContext.new()
        )
        registry = get_global_registry()
        with start_span(
            span_names.POST_DEMO_JOB_PROCESS,
            trace_context=trace_context,
            attributes={
                "live_demo.organization_id": str(principal.organization_id),
                "live_demo.session_id": str(session_id),
                "live_demo.operation": "run_full_post_demo_intelligence",
            },
        ):
            session = await db.scalar(
                select(DemoSession).where(
                    DemoSession.organization_id == principal.organization_id,
                    DemoSession.session_id == session_id,
                )
            )
            if session is None:
                raise NotFoundError("Session not found.", code="session_not_found")
            product = await db.scalar(
                select(Product).where(
                    Product.organization_id == principal.organization_id,
                    Product.product_id == session.product_id,
                )
            )
            if product is None:
                raise NotFoundError("Product not found.", code="product_not_found")

            job = await PostDemoJobRepository(db).upsert_running(
                organization_id=principal.organization_id,
                session_id=session_id,
                job_type="run_full_post_demo_intelligence",
                idempotency_key=f"session:{session_id}:post_demo:v1",
                trace_id=trace_id,
                max_attempts=settings.post_demo_max_attempts,
            )
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="post_demo.started",
                request_context=request_context,
                payload={"job_id": str(job.post_demo_job_id)},
            )
            with start_span(span_names.POST_DEMO_EVIDENCE_LOAD):
                bundle = await EvidenceLoader(db).load(
                    EvidenceLoadRequest(
                        organization_id=principal.organization_id,
                        session_id=session_id,
                        max_transcript_events=settings.lead_insight_max_transcript_events,
                        max_action_events=settings.lead_insight_max_action_events,
                        max_screen_events=settings.lead_insight_max_screen_events,
                        trace_id=trace_id,
                    )
                )
            with start_span(span_names.POST_DEMO_FEATURE_TRACK):
                features = FeatureShownTracker().track(bundle)
                feature_rows = await FeatureShownRepository(db).upsert_many(
                    organization_id=principal.organization_id,
                    session_id=session_id,
                    product_id=bundle.product_id,
                    features=features,
                )
            with start_span(span_names.POST_DEMO_INSIGHT_EXTRACT):
                insights = LeadInsightExtractor().extract(bundle)
                insight_rows = await LeadInsightPostDemoRepository(db).upsert_many(
                    organization_id=principal.organization_id,
                    session_id=session_id,
                    insights=insights,
                )
            with start_span(span_names.POST_DEMO_SUMMARY_GENERATE):
                summary, redaction_applied = LeadSummaryGenerator().generate(
                    bundle=bundle, insights=insights, features=features
                )
                qualification = summary.get("qualification", {})
                confidence = (
                    float(qualification.get("confidence", 0.0))
                    if isinstance(qualification, dict)
                    else 0.0
                )
                evidence_summary = summary.get("evidence_summary", {})
                lead_summary = await LeadSummaryPostDemoRepository(db).upsert_summary(
                    organization_id=principal.organization_id,
                    session_id=session_id,
                    summary=summary,
                    confidence=confidence,
                    evidence_summary=evidence_summary if isinstance(evidence_summary, dict) else {},
                    redaction_applied=redaction_applied,
                    generation_mode=settings.lead_summary_generation_mode,
                )
            crm_export_id = None
            if export_crm and settings.crm_export_enabled:
                if not can_export_crm(principal):
                    raise ForbiddenError(
                        "Missing CRM export permission.",
                        code="missing_crm_export_permission",
                    )
                with start_span(span_names.POST_DEMO_CRM_EXPORT):
                    result, export_row = await CrmExportService().export(
                        db,
                        organization_id=principal.organization_id,
                        session=session,
                        product=product,
                        lead_summary=lead_summary,
                        provider=crm_provider,
                        dry_run=settings.crm_export_dry_run,
                        trace_id=trace_id,
                    )
                crm_export_id = str(export_row.crm_export_id)
                await publish_event(
                    event_bus,
                    organization_id=principal.organization_id,
                    session_id=session_id,
                    event_type=(
                        "crm_export.dry_run_completed"
                        if result.status == "dry_run_completed"
                        else f"crm_export.{result.status}"
                    ),
                    request_context=request_context,
                    payload={"provider": crm_provider, "status": result.status},
                )
            await PostDemoJobRepository(db).mark_completed(
                job,
                metrics={
                    "insight_count": len(insight_rows),
                    "feature_count": len(feature_rows),
                    "crm_exported": bool(crm_export_id),
                },
            )
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="lead_insights.extracted",
                request_context=request_context,
                payload={"count": len(insight_rows)},
            )
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="features_shown.tracked",
                request_context=request_context,
                payload={"count": len(feature_rows)},
            )
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="lead_summary.ready",
                request_context=request_context,
                payload={"lead_summary_id": str(lead_summary.lead_summary_id)},
            )
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="post_demo.completed",
                request_context=request_context,
                payload={"job_id": str(job.post_demo_job_id)},
            )
            duration_seconds = (time.perf_counter_ns() - started_ns) / 1_000_000_000
            registry.increment(
                metric_names.POST_DEMO_JOBS_TOTAL,
                labels={"job_type": "run_full_post_demo_intelligence", "result": "success"},
            )
            registry.observe(
                metric_names.POST_DEMO_JOB_DURATION_SECONDS,
                duration_seconds,
                labels={"job_type": "run_full_post_demo_intelligence", "result": "success"},
            )
            await db.commit()
            return {
                "session_id": str(session_id),
                "status": "completed",
                "lead_summary_id": str(lead_summary.lead_summary_id),
                "crm_export_id": crm_export_id,
            }

    async def enqueue_full_run(
        self,
        redis: object,
        *,
        organization_id: UUID,
        session_id: UUID,
        trace_id: str,
    ) -> str:
        from redis.asyncio import Redis

        from live_demo_api.post_demo.post_demo_job_queue import PostDemoJobQueue

        assert isinstance(redis, Redis)
        envelope = PostDemoJobEnvelope.full_run(
            organization_id=organization_id,
            session_id=session_id,
            trace_id=trace_id,
            max_attempts=get_settings().post_demo_max_attempts,
        )
        return await PostDemoJobQueue(redis).enqueue(envelope)
