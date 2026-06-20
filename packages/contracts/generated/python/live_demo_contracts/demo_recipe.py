# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: F401

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


class DemoStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: UuidString
    step_order: int
    step_key: str
    goal: str
    screen_hint: str | None = None
    click_hint: str | None = None
    talk_track: str | None = None
    allowed_actions: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    fallback_strategy: str | None = None


class DemoRecipe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: UuidString
    product_id: UuidString
    recipe_name: str
    demo_goal: str
    steps: list[DemoStep]
    never_click: list[str] = Field(default_factory=list)
    created_at: IsoDateTimeString
    updated_at: IsoDateTimeString


class RecipeValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: list[str] = Field(default_factory=list)
