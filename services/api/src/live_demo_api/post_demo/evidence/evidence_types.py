"""Typed post-demo evidence records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class EvidenceLoadRequest:
    organization_id: UUID
    session_id: UUID
    max_transcript_events: int
    max_action_events: int
    max_screen_events: int
    trace_id: str


@dataclass(frozen=True, slots=True)
class TranscriptEvidence:
    transcript_event_id: UUID
    speaker: str
    chunk_type: str
    text: str
    is_final: bool
    turn_id: UUID | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ActionEvidence:
    action_event_id: UUID
    action_type: str
    action_payload: dict[str, object]
    risk_level: str
    policy_decision: str
    success: bool | None
    from_screen_id: UUID | None
    to_screen_id: UUID | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ScreenEvidence:
    screen_id: UUID
    screen_hash: str
    url: str | None
    title: str | None
    summary: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RecipeStepEvidence:
    recipe_step_progress_id: UUID
    recipe_id: UUID
    step_id: UUID
    step_key: str
    status: str
    matched_screen_id: UUID | None
    matched_action_id: str | None
    matched_confidence: float
    evidence: dict[str, object]
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class LeadInsightEvidence:
    insight_id: UUID
    insight_type: str
    content: str
    confidence: float
    evidence_transcript_event_ids: tuple[UUID, ...]
    evidence_browser_action_ids: tuple[UUID, ...]
    evidence_screen_ids: tuple[UUID, ...]
    evidence_recipe_step_ids: tuple[UUID, ...]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SessionEvidenceBundle:
    organization_id: UUID
    session_id: UUID
    product_id: UUID
    transcript_events: tuple[TranscriptEvidence, ...]
    action_events: tuple[ActionEvidence, ...]
    screen_events: tuple[ScreenEvidence, ...]
    recipe_progress: tuple[RecipeStepEvidence, ...]
    existing_insights: tuple[LeadInsightEvidence, ...]
    loaded_at: datetime
