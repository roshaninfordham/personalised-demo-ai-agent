"""Map ORM records to generated contract DTOs."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from live_demo_api.db.models import (
    ActionEvent,
    DemoRecipe,
    DemoSession,
    DemoStep,
    LeadInsight,
    LeadSummary,
    Product,
    ProductGuidance,
    TranscriptEvent,
)
from live_demo_contracts.browser_action import BrowserActionEventResponse
from live_demo_contracts.common import (
    DemoPhase,
    JsonValue,
    PolicyDecision,
    ProductConfiguration,
    ProductGuidanceResponse,
    ProductGuidanceType,
    ProductResponse,
    RiskLevel,
    SessionStatus,
)
from live_demo_contracts.demo_recipe import DemoRecipe as DemoRecipeContract
from live_demo_contracts.demo_recipe import DemoStep as DemoStepContract
from live_demo_contracts.demo_recipe import RecipeStatus
from live_demo_contracts.demo_session import DemoSession as DemoSessionContract
from live_demo_contracts.lead_summary import (
    CrmPayload,
    DemoSummary,
    InsightType,
    Qualification,
)
from live_demo_contracts.lead_summary import (
    LeadInsight as LeadInsightContract,
)
from live_demo_contracts.lead_summary import (
    LeadSummary as LeadSummaryContract,
)
from live_demo_contracts.transcript import (
    TranscriptChunkType,
    TranscriptSpeaker,
)
from live_demo_contracts.transcript import (
    TranscriptEvent as TranscriptEventContract,
)


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return str(value.isoformat())


def as_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def product_to_response(product: Product) -> ProductResponse:
    configuration = ProductConfiguration.model_validate(product.configuration or {})
    return ProductResponse(
        product_id=str(product.product_id),
        product_name=product.product_name,
        product_url=product.product_url,
        default_persona=product.default_persona,
        product_summary=product.product_summary,
        confidence=as_float(product.confidence),
        configuration=configuration,
        created_at=cast(str, iso(product.created_at)),
        updated_at=cast(str, iso(product.updated_at)),
    )


def guidance_to_response(row: ProductGuidance) -> ProductGuidanceResponse:
    return ProductGuidanceResponse(
        guidance_id=str(row.guidance_id),
        product_id=str(row.product_id),
        guidance_type=ProductGuidanceType(row.guidance_type),
        title=row.title,
        content=cast(dict[str, JsonValue], row.content),
        source_uri=row.source_uri,
        created_at=cast(str, iso(row.created_at)),
        updated_at=cast(str, iso(row.updated_at)),
    )


def step_to_response(step: DemoStep) -> DemoStepContract:
    return DemoStepContract(
        step_id=str(step.step_id),
        step_order=step.step_order,
        step_key=step.step_key,
        goal=step.goal,
        screen_hint=step.screen_hint,
        click_hint=step.click_hint,
        talk_track=step.talk_track,
        allowed_actions=step.allowed_actions,
        success_criteria=step.success_criteria,
        fallback_strategy=step.fallback_strategy,
    )


def recipe_to_response(recipe: DemoRecipe, steps: list[DemoStep]) -> DemoRecipeContract:
    return DemoRecipeContract(
        recipe_id=str(recipe.recipe_id),
        product_id=str(recipe.product_id),
        recipe_name=recipe.recipe_name,
        target_persona=recipe.target_persona,
        demo_goal=recipe.demo_goal,
        status=RecipeStatus(recipe.status),
        is_active=recipe.is_active,
        steps=[step_to_response(step) for step in steps],
        never_click=recipe.never_click,
        global_talk_track=recipe.global_talk_track,
        created_at=cast(str, iso(recipe.created_at)),
        updated_at=cast(str, iso(recipe.updated_at)),
    )


def session_to_response(session: DemoSession) -> DemoSessionContract:
    return DemoSessionContract(
        session_id=str(session.session_id),
        product_id=str(session.product_id),
        recipe_id=str(session.recipe_id) if session.recipe_id is not None else None,
        status=SessionStatus(session.status),
        current_phase=DemoPhase(session.current_phase),
        start_url=session.start_url,
        user_persona=session.user_persona,
        user_company=session.user_company,
        user_display_name=session.user_display_name,
        user_email=session.user_email,
        transport_session_id=session.transport_session_id,
        created_at=cast(str, iso(session.created_at)),
        updated_at=cast(str, iso(session.updated_at)),
        started_at=iso(session.started_at),
        ended_at=iso(session.ended_at),
    )


def transcript_to_response(row: TranscriptEvent) -> TranscriptEventContract:
    return TranscriptEventContract(
        transcript_event_id=str(row.transcript_event_id),
        session_id=str(row.session_id),
        speaker=TranscriptSpeaker(row.speaker),
        chunk_type=TranscriptChunkType(row.chunk_type),
        text=row.text,
        created_at=cast(str, iso(row.created_at)),
        start_ms=row.start_ms,
        end_ms=row.end_ms,
        confidence=as_float(row.confidence) if row.confidence is not None else None,
        turn_id=str(row.turn_id) if row.turn_id is not None else None,
    )


def action_to_response(row: ActionEvent, *, include_payload: bool) -> BrowserActionEventResponse:
    return BrowserActionEventResponse(
        action_event_id=str(row.action_event_id),
        action_type=row.action_type,
        risk_level=RiskLevel(row.risk_level),
        policy_decision=PolicyDecision(row.policy_decision),
        success=row.success,
        error_code=row.error_code,
        from_screen_id=str(row.from_screen_id) if row.from_screen_id is not None else None,
        to_screen_id=str(row.to_screen_id) if row.to_screen_id is not None else None,
        latency_ms=row.latency_ms,
        created_at=cast(str, iso(row.created_at)),
        action_payload=cast(dict[str, JsonValue], row.action_payload) if include_payload else None,
    )


def insight_to_response(row: LeadInsight) -> LeadInsightContract:
    return LeadInsightContract(
        insight_id=str(row.insight_id),
        insight_type=InsightType(row.insight_type),
        value=row.content,
        confidence=as_float(row.confidence),
        evidence_transcript_event_ids=[str(item) for item in row.evidence_transcript_event_ids],
        evidence_browser_action_ids=[str(item) for item in row.evidence_browser_action_ids],
        evidence_screen_ids=[str(item) for item in row.evidence_screen_ids],
        created_at=cast(str, iso(row.created_at)),
    )


def lead_summary_to_response(row: LeadSummary) -> LeadSummaryContract:
    summary = row.summary
    demo_summary_payload = summary.get("demo_summary", {})
    if isinstance(demo_summary_payload, dict):
        features_payload = demo_summary_payload.get("features_shown", [])
        features_shown = [
            str(item.get("feature_label", item.get("feature_key", "")))
            if isinstance(item, dict)
            else str(item)
            for item in features_payload
        ]
        questions_payload = demo_summary_payload.get("questions_asked", [])
        questions_asked = [
            str(item.get("content", item.get("question", "")))
            if isinstance(item, dict)
            else str(item)
            for item in questions_payload
        ]
        evidence_payload = summary.get("evidence_summary", {})
        screen_ids = demo_summary_payload.get("screens_visited", [])
        if not screen_ids and isinstance(evidence_payload, dict):
            screen_ids = evidence_payload.get("screen_ids", [])
        demo_summary = {
            "duration_seconds": int(demo_summary_payload.get("duration_seconds", 0) or 0),
            "features_shown": [item for item in features_shown if item],
            "questions_asked": [item for item in questions_asked if item],
            "screens_visited": [str(item) for item in screen_ids],
        }
    else:
        demo_summary = {}

    qualification_payload = summary.get("qualification", {})
    if isinstance(qualification_payload, dict):
        urgency_payload = qualification_payload.get(
            "urgency", qualification_payload.get("urgency_level", {})
        )
        if isinstance(urgency_payload, dict):
            urgency_level = str(urgency_payload.get("level", "unknown"))
        else:
            urgency_level = str(urgency_payload or "unknown")
        qualification = {
            "insights": [],
            "urgency_level": urgency_level,
            "confidence": float(qualification_payload.get("confidence", 0.0) or 0.0),
        }
    else:
        qualification = {}

    follow_up_payload: Any = summary.get("recommended_follow_up", "")
    if isinstance(follow_up_payload, dict):
        recommended_follow_up = str(follow_up_payload.get("summary", ""))
    else:
        recommended_follow_up = str(follow_up_payload)

    return LeadSummaryContract(
        lead_summary_id=str(row.lead_summary_id),
        session_id=str(row.session_id),
        demo_summary=DemoSummary.model_validate(demo_summary),
        qualification=Qualification.model_validate(qualification),
        recommended_follow_up=recommended_follow_up,
        crm_payload=CrmPayload.model_validate(
            summary.get("crm_payload", {"provider": "mock", "objects": []})
        ),
        created_at=cast(str, iso(row.created_at)),
    )
