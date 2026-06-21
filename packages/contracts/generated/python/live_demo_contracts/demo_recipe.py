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


class RecipeStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class RecipeProgressStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    ADAPTED = "adapted"
    BLOCKED = "blocked"


class RecipeDemoPhase(StrEnum):
    START = "START"
    DISCOVERY = "DISCOVERY"
    OVERVIEW = "OVERVIEW"
    CORE_WORKFLOW = "CORE_WORKFLOW"
    DEEP_DIVE = "DEEP_DIVE"
    Q_AND_A = "Q_AND_A"
    SUMMARY = "SUMMARY"
    END = "END"
    RECOVERY = "RECOVERY"


class RecipeValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    code: str
    message: str
    severity: Literal["error", "warning"] = "error"


class AllowedFormFieldInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_label_pattern: str
    field_type: str = "text"
    max_chars: int = 120


class ConfirmationRequiredActionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: str
    label_pattern: str
    reason: str


class DemoStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: UuidString
    step_order: int
    step_key: str
    goal: str
    phase: RecipeDemoPhase | None = None
    screen_hint: str | None = None
    click_hint: str | None = None
    talk_track: str | None = None
    allowed_actions: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    fallback_strategy: str | None = None
    max_attempts: int = 2
    required: bool = True
    confidence: float = 1.0
    source_references: list[str] = Field(default_factory=list)


class DemoStepInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_order: int
    step_key: str
    goal: str
    phase: RecipeDemoPhase | None = None
    screen_hint: str | None = None
    click_hint: str | None = None
    talk_track: str | None = None
    allowed_actions: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    fallback_strategy: str | None = None
    max_attempts: int = 2
    required: bool = True
    confidence: float = 1.0
    source_references: list[str] = Field(default_factory=list)


class CreateDemoRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_name: str
    target_persona: str | None = None
    demo_goal: str
    never_click: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    allowed_form_fields: list[AllowedFormFieldInput] = Field(default_factory=list)
    confirmation_required_actions: list[ConfirmationRequiredActionInput] = Field(default_factory=list)
    global_talk_track: str | None = None
    steps: list[DemoStepInput]


class UpdateDemoRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_name: str | None = None
    target_persona: str | None = None
    demo_goal: str | None = None
    never_click: list[str] | None = None
    allowed_domains: list[str] | None = None
    allowed_form_fields: list[AllowedFormFieldInput] | None = None
    confirmation_required_actions: list[ConfirmationRequiredActionInput] | None = None
    global_talk_track: str | None = None
    steps: list[DemoStepInput] | None = None


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


class ValidateDemoRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe: dict[str, JsonValue]


class ValidateDemoRecipeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: list[RecipeValidationIssue] = Field(default_factory=list)
    warnings: list[RecipeValidationIssue] = Field(default_factory=list)
    normalized_recipe: CreateDemoRecipeRequest | None | None = None


class GenerateDemoRecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_persona: str | None = None
    text_guidance: str


class GenerateDemoRecipeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe: CreateDemoRecipeRequest
    validation: ValidateDemoRecipeResponse
    generation_run_id: UuidString
    recipe_id: UuidString | None | None = None
    status: str


class CompiledDemoRecipeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compiled_recipe_id: UuidString
    recipe_id: UuidString
    recipe_hash: str
    compiled_hash: str
    compiled_payload: dict[str, JsonValue]
    status: str


class RecipeStepProgressResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_key: str
    status: RecipeProgressStatus
    attempt_count: int
    matched_screen_id: str | None = None
    matched_action_id: str | None = None
    matched_confidence: float
    failure_reason: str | None = None
    evidence: dict[str, JsonValue] = Field(default_factory=dict)


class RecipeProgressResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UuidString
    recipe_id: UuidString
    active_step_key: str | None
    steps: list[RecipeStepProgressResponse] = Field(default_factory=list)
    completed_count: int
    total_count: int
    progress_ratio: float


class ActivateDemoRecipeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe: DemoRecipe


class ListDemoRecipesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DemoRecipe] = Field(default_factory=list)
    next_cursor: str | None
