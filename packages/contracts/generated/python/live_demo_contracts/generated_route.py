# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: E501, F401, RUF100

from __future__ import annotations

from enum import StrEnum
from typing import Literal

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


class GeneratedDemoRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route_id: str
    route_name: str
    route_type: Literal["generated", "manual", "hybrid"]
    status: Literal["draft", "active", "archived", "invalid"]
    confidence: float
    summary: str | None | None = None
    steps: list[dict[str, JsonValue]]
