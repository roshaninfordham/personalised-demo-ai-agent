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


class ProductLearningRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    learning_run_id: str
    organization_id: str
    product_id: str
    session_id: str | None | None = None
    start_url: str
    status: Literal["pending", "running", "completed", "failed", "cancelled", "dead_letter"]
    trigger_type: Literal["product_created", "session_created", "manual", "recipe_missing", "screen_unknown", "scheduled_refresh"]
    attempt_count: int
    max_attempts: int
    error_code: str | None | None = None
    metrics: dict[str, JsonValue] | None = None
    created_at: str
    updated_at: str
