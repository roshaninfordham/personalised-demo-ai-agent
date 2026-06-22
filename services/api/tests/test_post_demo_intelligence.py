from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from live_demo_api.db.models import DemoSession, LeadSummary, Product
from live_demo_api.post_demo.crm.crm_export_policy import can_export_crm
from live_demo_api.post_demo.crm.crm_export_service import CrmAdapterRegistry, payload_hash
from live_demo_api.post_demo.crm.crm_payload_mapper import CrmPayloadMapper
from live_demo_api.post_demo.crm.crm_types import CrmExportRequest
from live_demo_api.post_demo.crm.mock_crm_adapter import MockCrmAdapter
from live_demo_api.post_demo.evidence.evidence_types import (
    ActionEvidence,
    RecipeStepEvidence,
    ScreenEvidence,
    SessionEvidenceBundle,
    TranscriptEvidence,
)
from live_demo_api.post_demo.features.feature_shown_tracker import FeatureShownTracker
from live_demo_api.post_demo.insights.lead_insight_extractor import LeadInsightExtractor
from live_demo_api.post_demo.summaries.lead_summary_generator import LeadSummaryGenerator
from live_demo_api.post_demo.summaries.summary_validator import SummaryValidator
from live_demo_api.security import Principal

ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


def _bundle() -> SessionEvidenceBundle:
    now = datetime.now(UTC)
    session_id = uuid4()
    product_id = uuid4()
    screen_id = uuid4()
    action_id = uuid4()
    transcript_events = (
        TranscriptEvidence(
            transcript_event_id=uuid4(),
            speaker="user",
            chunk_type="final",
            text="I'm a founder and it takes too long to build weekly reports.",
            is_final=True,
            turn_id=None,
            created_at=now,
        ),
        TranscriptEvidence(
            transcript_event_id=uuid4(),
            speaker="user",
            chunk_type="final",
            text="Can we export reports this week?",
            is_final=True,
            turn_id=None,
            created_at=now,
        ),
        TranscriptEvidence(
            transcript_event_id=uuid4(),
            speaker="user",
            chunk_type="final",
            text="I'm concerned about security.",
            is_final=True,
            turn_id=None,
            created_at=now,
        ),
        TranscriptEvidence(
            transcript_event_id=uuid4(),
            speaker="assistant",
            chunk_type="final",
            text="I can't verify security controls from this screen.",
            is_final=True,
            turn_id=None,
            created_at=now,
        ),
    )
    return SessionEvidenceBundle(
        organization_id=ORG_ID,
        session_id=session_id,
        product_id=product_id,
        transcript_events=transcript_events,
        action_events=(
            ActionEvidence(
                action_event_id=action_id,
                action_type="click_element",
                action_payload={"label": "Reports"},
                risk_level="low",
                policy_decision="allowed",
                success=True,
                from_screen_id=screen_id,
                to_screen_id=screen_id,
                created_at=now,
            ),
        ),
        screen_events=(
            ScreenEvidence(
                screen_id=screen_id,
                screen_hash="screen_reports",
                url="https://example.com/reports",
                title="Reports",
                summary="Reports export and analytics.",
                created_at=now,
            ),
        ),
        recipe_progress=(
            RecipeStepEvidence(
                recipe_step_progress_id=uuid4(),
                recipe_id=uuid4(),
                step_id=uuid4(),
                step_key="reports",
                status="completed",
                matched_screen_id=screen_id,
                matched_action_id=str(action_id),
                matched_confidence=0.9,
                evidence={"goal": "Show Reports"},
                updated_at=now,
            ),
        ),
        existing_insights=(),
        loaded_at=now,
    )


def test_lead_insight_extractor_finds_evidence_backed_sales_signals() -> None:
    insights = LeadInsightExtractor().extract(_bundle())
    by_type = {insight.insight_type: insight for insight in insights}

    assert "role" in by_type
    assert "pain_point" in by_type
    assert "buying_signal" in by_type
    assert "urgency" in by_type
    assert "feature_interest" in by_type
    assert "objection" in by_type
    assert "unanswered_question" in by_type
    assert all(insight.evidence_transcript_event_ids for insight in insights)


def test_feature_shown_tracker_merges_screen_action_and_recipe_evidence() -> None:
    features = FeatureShownTracker().track(_bundle())
    reports = next(
        feature
        for feature in features
        if feature.feature_category == "reporting" and feature.evidence_browser_action_ids
    )

    assert reports.confidence >= 0.45
    assert reports.evidence_screen_ids
    assert reports.evidence_browser_action_ids
    assert any(feature.evidence_recipe_step_ids for feature in features)


def test_lead_summary_generator_is_evidence_backed_and_schema_valid() -> None:
    bundle = _bundle()
    insights = LeadInsightExtractor().extract(bundle)
    features = FeatureShownTracker().track(bundle)

    summary, redaction_applied = LeadSummaryGenerator().generate(
        bundle=bundle,
        insights=insights,
        features=features,
    )

    assert SummaryValidator().validate(summary)
    assert isinstance(redaction_applied, bool)
    assert summary["evidence_summary"]["transcript_event_ids"]
    assert summary["qualification"]["overall_score"] > 0


def test_crm_payload_mapping_hash_and_mock_adapter_are_deterministic() -> None:
    bundle = _bundle()
    insights = LeadInsightExtractor().extract(bundle)
    features = FeatureShownTracker().track(bundle)
    summary, _ = LeadSummaryGenerator().generate(
        bundle=bundle,
        insights=insights,
        features=features,
    )
    session = DemoSession(
        organization_id=ORG_ID,
        session_id=bundle.session_id,
        product_id=bundle.product_id,
        status="completed",
        current_phase="summary",
        start_url="https://example.com",
        user_persona="founder",
        user_company="Example Co",
        user_display_name="Jane Founder",
        user_email="jane@example.com",
    )
    product = Product(
        organization_id=ORG_ID,
        product_id=bundle.product_id,
        product_name="Example Product",
        product_url="https://example.com",
        default_persona="founder",
    )
    lead_summary = LeadSummary(
        organization_id=ORG_ID,
        session_id=bundle.session_id,
        lead_summary_id=uuid4(),
        summary=summary,
        confidence=Decimal("0.800"),
    )
    payload = CrmPayloadMapper().map_payload(
        lead_summary=lead_summary,
        session=session,
        product=product,
    )

    assert payload_hash(payload) == payload_hash(payload)
    adapter = MockCrmAdapter()
    result = asyncio.run(
        adapter.export(
            CrmExportRequest(
                organization_id=ORG_ID,
                session_id=bundle.session_id,
                lead_summary_id=lead_summary.lead_summary_id,
                payload=payload,
                dry_run=True,
                idempotency_key="test-idempotency",
                trace_id="trace_test",
            )
        )
    )
    assert result.status == "dry_run_completed"
    assert result.external_object_ids["contact"].startswith("mock_contact_")


def test_crm_adapter_registry_and_policy_fail_closed_for_unsupported_roles() -> None:
    registry = CrmAdapterRegistry()

    assert registry.get_adapter("mock").provider_name == "mock"
    assert registry.get_adapter("hubspot").provider_name == "hubspot"
    assert not can_export_crm(
        Principal(
            organization_id=ORG_ID,
            user_id=uuid4(),
            role="viewer",
            actor_type="user",
        )
    )
