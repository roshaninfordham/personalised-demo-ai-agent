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


class RecipeStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


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


class DemoStepInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
    target_persona: str | None = None
    demo_goal: str
    status: RecipeStatus
    is_active: bool
    steps: list[DemoStep]
    never_click: list[str] = Field(default_factory=list)
    global_talk_track: str | None = None
    created_at: IsoDateTimeString
    updated_at: IsoDateTimeString


class CreateDemoRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_name: str
    target_persona: str | None = None
    demo_goal: str
    never_click: list[str] = Field(default_factory=list)
    global_talk_track: str | None = None
    steps: list[DemoStepInput]


class UpdateDemoRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_name: str | None = None
    target_persona: str | None = None
    demo_goal: str | None = None
    never_click: list[str] | None = None
    global_talk_track: str | None = None
    steps: list[DemoStepInput] | None = None


type DemoRecipeResponse = DemoRecipe


class ListDemoRecipesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DemoRecipe] = Field(default_factory=list)
    next_cursor: str | None


class RecipeValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    code: str
    message: str


class RecipeValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: list[str] = Field(default_factory=list)


class ValidateDemoRecipeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: list[RecipeValidationIssue] = Field(default_factory=list)
    warnings: list[RecipeValidationIssue] = Field(default_factory=list)


class ActivateDemoRecipeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe: DemoRecipe
