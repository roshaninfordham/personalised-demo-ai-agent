# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: E501, F401, RUF100

from __future__ import annotations

from enum import StrEnum

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


class FeatureShownRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature_shown_id: UuidString
    feature_key: str
    feature_label: str
    feature_category: str | None | None = None
    confidence: float
    source_type: str
    evidence: FeatureEvidenceRefs


class FeatureEvidenceRefs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript_event_ids: list[UuidString] = Field(default_factory=list)
    browser_action_ids: list[UuidString] = Field(default_factory=list)
    screen_ids: list[UuidString] = Field(default_factory=list)
    recipe_step_ids: list[UuidString] = Field(default_factory=list)


class FeatureShownRecordsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[FeatureShownRecord] = Field(default_factory=list)
