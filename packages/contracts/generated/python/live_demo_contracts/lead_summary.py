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


class InsightType(StrEnum):
    PAIN_POINT = "pain_point"
    USE_CASE = "use_case"
    OBJECTION = "objection"
    BUYING_SIGNAL = "buying_signal"
    QUESTION = "question"
    FEATURE_INTEREST = "feature_interest"
    PERSONA = "persona"
    URGENCY = "urgency"


class LeadInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    insight_id: UuidString
    insight_type: InsightType
    value: str
    confidence: float
    evidence_transcript_event_ids: list[UuidString] = Field(default_factory=list)
    evidence_browser_action_ids: list[UuidString] = Field(default_factory=list)
    evidence_screen_ids: list[UuidString] = Field(default_factory=list)
    created_at: IsoDateTimeString


class DemoSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_seconds: int
    features_shown: list[str] = Field(default_factory=list)
    questions_asked: list[str] = Field(default_factory=list)
    screens_visited: list[UuidString] = Field(default_factory=list)


class Qualification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    insights: list[LeadInsight] = Field(default_factory=list)
    urgency_level: str
    confidence: float


class CrmObject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_type: str
    properties: Metadata


class CrmPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    objects: list[CrmObject] = Field(default_factory=list)


class LeadSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead_summary_id: UuidString
    session_id: UuidString
    demo_summary: DemoSummary
    qualification: Qualification
    recommended_follow_up: str
    crm_payload: CrmPayload
    created_at: IsoDateTimeString


class LeadInsightsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[LeadInsight] = Field(default_factory=list)
    next_cursor: str | None


class LeadSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead_summary: LeadSummary


class CrmPayloadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crm_payload: CrmPayload


class FeatureShown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    source: str
    screen_id: UuidString | None = None
    action_event_id: UuidString | None = None


class FeaturesShownResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    features: list[FeatureShown] = Field(default_factory=list)
    source: str
    message: str
