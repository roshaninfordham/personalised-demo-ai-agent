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


class RecipeMatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matched: bool
    step_key: str
    screen_id: str | None = None
    action_id: str | None = None
    confidence: float
    decision: str
    reason_codes: list[str] = Field(default_factory=list)
