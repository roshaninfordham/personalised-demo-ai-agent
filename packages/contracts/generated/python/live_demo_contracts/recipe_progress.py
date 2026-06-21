# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: E501, F401, RUF100

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

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


class RecipeProgressEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UuidString
    recipe_id: UuidString
    step_key: str
    status: str
