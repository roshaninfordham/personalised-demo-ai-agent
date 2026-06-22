# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: E501, F401, RUF100

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from live_demo_contracts.common import (
    BoundingBox,
    DemoPhase,
    IsoDateTimeString,
    JsonValue,
    Metadata,
    PolicyDecision,
    ProviderName,
    RiskLevel,
    SessionStatus,
    TraceId,
    UuidString,
)


class PostDemoInsightType(StrEnum):
    PAIN_POINT = "pain_point"
    OBJECTION = "objection"
    BUYING_SIGNAL = "buying_signal"
    ROLE = "role"
    URGENCY = "urgency"
    FEATURE_INTEREST = "feature_interest"
    UNANSWERED_QUESTION = "unanswered_question"
    QUESTION = "question"
    USE_CASE = "use_case"
    DECISION_CRITERIA = "decision_criteria"
    NEXT_STEP = "next_step"


class EvidenceRefs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript_event_ids: list[UuidString] = Field(default_factory=list)
    browser_action_ids: list[UuidString] = Field(default_factory=list)
    screen_ids: list[UuidString] = Field(default_factory=list)
    recipe_step_ids: list[UuidString] = Field(default_factory=list)


class ExtractedLeadInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    insight_type: PostDemoInsightType
    content: str
    confidence: float
    importance: float
    evidence: EvidenceRefs
    source: str
