"""Lead insight, lead-summary, and CRM payload API routes."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.dependencies import (
    get_current_principal,
    get_db_session,
    get_event_bus,
    get_request_context,
)
from live_demo_api.errors import NotFoundError
from live_demo_api.events.event_bus import EventBus
from live_demo_api.post_demo.post_demo_orchestrator import PostDemoOrchestrator
from live_demo_api.post_demo.repositories.crm_exports import CrmExportRepository
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.lead_summary_service import LeadSummaryService
from live_demo_contracts.lead_summary import (
    CrmPayloadResponse,
    LeadInsightsResponse,
    LeadSummaryResponse,
)

router = APIRouter(prefix="/api/v1/demo-sessions/{session_id}", tags=["lead-summaries"])


@router.post("/post-demo/run")
async def run_post_demo(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = body or {}
    return await PostDemoOrchestrator().run_full(
        db,
        event_bus,
        principal,
        request_context,
        session_id=session_id,
        export_crm=bool(payload.get("export_crm", False)),
        crm_provider=str(payload.get("crm_provider") or "mock"),
    )


@router.get("/lead-insights", response_model=LeadInsightsResponse)
async def get_lead_insights(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    insight_type: str | None = None,
    min_confidence: float | None = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> LeadInsightsResponse:
    return await LeadSummaryService().list_insights(
        db,
        principal,
        session_id,
        insight_type=insight_type,
        min_confidence=min_confidence,
        limit=limit,
        cursor=cursor,
    )


@router.get("/lead-summary", response_model=LeadSummaryResponse)
async def get_lead_summary(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> LeadSummaryResponse:
    return await LeadSummaryService().get_summary(db, principal, session_id)


@router.post("/lead-summary/regenerate")
async def regenerate_lead_summary(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> dict[str, Any]:
    return await PostDemoOrchestrator().run_full(
        db,
        event_bus,
        principal,
        request_context,
        session_id=session_id,
        export_crm=False,
        crm_provider="mock",
    )


@router.get("/crm-payload", response_model=CrmPayloadResponse)
async def get_crm_payload(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> CrmPayloadResponse:
    return await LeadSummaryService().get_crm_payload(db, principal, session_id)


@router.post("/crm-export")
async def export_crm(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = body or {}
    return await PostDemoOrchestrator().run_full(
        db,
        event_bus,
        principal,
        request_context,
        session_id=session_id,
        export_crm=True,
        crm_provider=str(payload.get("crm_provider") or "mock"),
    )


@router.get("/crm-exports")
async def list_crm_exports(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> dict[str, Any]:
    rows = await CrmExportRepository(db).list_for_session(
        organization_id=principal.organization_id,
        session_id=session_id,
    )
    return {
        "items": [
            {
                "crm_export_id": str(row.crm_export_id),
                "provider": row.provider,
                "status": row.status,
                "dry_run": row.dry_run,
                "external_object_ids": row.external_object_ids,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.get("/crm-exports/{crm_export_id}")
async def get_crm_export(
    session_id: UUID,
    crm_export_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> dict[str, Any]:
    row = await CrmExportRepository(db).get_for_session(
        organization_id=principal.organization_id,
        session_id=session_id,
        crm_export_id=crm_export_id,
    )
    if row is None:
        raise NotFoundError("CRM export not found.", code="crm_export_not_found")
    return {
        "crm_export_id": str(row.crm_export_id),
        "provider": row.provider,
        "status": row.status,
        "dry_run": row.dry_run,
        "external_object_ids": row.external_object_ids,
        "payload": row.redacted_payload or {},
        "created_at": row.created_at.isoformat(),
        "sent_at": row.sent_at.isoformat() if row.sent_at is not None else None,
    }
