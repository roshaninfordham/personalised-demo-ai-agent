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


class CompiledRecipeStatus(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    INVALID = "invalid"
    ARCHIVED = "archived"


class CompiledRecipeArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: UuidString
    recipe_hash: str
    compiled_hash: str
    compiled_payload: dict[str, JsonValue]
    status: CompiledRecipeStatus
