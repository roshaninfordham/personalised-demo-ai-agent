from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

DemoPhase = Literal[
    "START",
    "DISCOVERY",
    "OVERVIEW",
    "CORE_WORKFLOW",
    "DEEP_DIVE",
    "Q_AND_A",
    "SUMMARY",
    "END",
    "RECOVERY",
]

ProgressStatus = Literal[
    "pending",
    "in_progress",
    "completed",
    "skipped",
    "failed",
    "adapted",
    "blocked",
]


@dataclass(frozen=True, slots=True)
class RecipeEngineLimits:
    max_steps: int = 50
    max_never_click_items: int = 100
    max_allowed_actions: int = 100
    max_allowed_domains: int = 50
    max_allowed_form_fields: int = 100
    max_text_field_chars: int = 2000
    max_json_bytes: int = 262_144
    max_json_depth: int = 12
    max_json_keys: int = 5000
    max_compiled_payload_bytes: int = 65_536
    match_max_candidate_screens: int = 50
    match_max_candidate_actions: int = 50
    screen_match_threshold: float = 0.72
    action_match_threshold: float = 0.70
    fallback_max_attempts: int = 2


@dataclass(frozen=True, slots=True)
class RecipeValidationIssue:
    path: str
    code: str
    message: str
    severity: Literal["error", "warning"] = "error"


@dataclass(frozen=True, slots=True)
class RecipeValidationResult:
    valid: bool
    errors: tuple[RecipeValidationIssue, ...]
    warnings: tuple[RecipeValidationIssue, ...] = ()
    normalized_recipe: DemoRecipe | None = None


@dataclass(frozen=True, slots=True)
class AllowedFormField:
    field_label_pattern: str
    field_type: str = "text"
    max_chars: int = 120


@dataclass(frozen=True, slots=True)
class ConfirmationRequiredAction:
    action_type: str
    label_pattern: str
    reason: str


@dataclass(frozen=True, slots=True)
class DemoRecipeStep:
    step_order: int
    step_key: str
    goal: str
    phase: DemoPhase | None = None
    screen_hint: str | None = None
    click_hint: str | None = None
    talk_track: str | None = None
    allowed_actions: tuple[str, ...] = ()
    success_criteria: tuple[str, ...] = ()
    fallback_strategy: str | None = None
    max_attempts: int = 2
    required: bool = True
    confidence: float = 1.0
    source_references: tuple[str, ...] = ()
    step_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True, slots=True)
class DemoRecipe:
    recipe_name: str
    demo_goal: str
    steps: tuple[DemoRecipeStep, ...]
    target_persona: str | None = None
    global_talk_track: str | None = None
    never_click: tuple[str, ...] = ()
    allowed_domains: tuple[str, ...] = ()
    allowed_form_fields: tuple[AllowedFormField, ...] = ()
    confirmation_required_actions: tuple[ConfirmationRequiredAction, ...] = ()
    status: Literal["draft", "active", "archived"] = "draft"


@dataclass(frozen=True, slots=True)
class CompiledRecipeStep:
    step_id: UUID
    step_order: int
    step_key: str
    phase: DemoPhase
    required: bool
    goal: str
    screen_hint_tokens: frozenset[str]
    click_hint_tokens: frozenset[str]
    talk_track: str | None
    allowed_tool_names: frozenset[str]
    success_criteria: tuple[str, ...]
    fallback_strategy: str
    max_attempts: int
    source_confidence: float


@dataclass(frozen=True, slots=True)
class CompiledAllowedAction:
    action_type: str
    label_pattern: str
    risk_level_max: str = "medium"


@dataclass(frozen=True, slots=True)
class CompiledRecipeSafetyPolicy:
    never_click: tuple[str, ...]
    allowed_domains: tuple[str, ...]
    allowed_form_fields: tuple[AllowedFormField, ...]
    confirmation_required_actions: tuple[ConfirmationRequiredAction, ...]


@dataclass(frozen=True, slots=True)
class CompiledDomainPolicy:
    exact_domains: tuple[str, ...]
    wildcard_suffixes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompiledFallbackStrategy:
    step_key: str
    strategy: str
    max_attempts: int


@dataclass(frozen=True, slots=True)
class CompiledRecipe:
    recipe_id: UUID
    product_id: UUID
    recipe_hash: str
    compiled_hash: str
    version: int
    steps_by_order: tuple[CompiledRecipeStep, ...]
    step_by_key: dict[str, CompiledRecipeStep]
    safety_policy: CompiledRecipeSafetyPolicy
    allowed_action_index: dict[str, CompiledAllowedAction]
    never_click_matcher_payload: dict[str, Any]
    domain_policy: CompiledDomainPolicy
    success_criteria_by_step: dict[str, tuple[str, ...]]
    fallback_by_step: dict[str, CompiledFallbackStrategy]
    context_payload: dict[str, Any]
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class CompileRecipeRequest:
    organization_id: UUID
    product_id: UUID
    recipe_id: UUID
    normalized_recipe: DemoRecipe
    product_url: str
    global_policy_version: str = "phase_9"
    trace_id: str = ""
    version: int = 1


@dataclass(frozen=True, slots=True)
class SafeActionContext:
    action_id: str
    action_type: str
    label: str | None = None
    element_id: str | None = None
    risk_level: str = "unknown"
    score: float = 0.0
    requires_confirmation: bool = False
    reason: str | None = None
    expires_at: datetime | None = None
    visible: bool = True
    enabled: bool = True
    historical_success: float = 0.5


@dataclass(frozen=True, slots=True)
class ScreenContext:
    screen_id: str
    screen_hash: str
    url_path: str | None = None
    title: str | None = None
    summary: str | None = None
    visible_text: str | None = None
    screen_type: str | None = None
    confidence: float = 0.0
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ScreenNodeContext:
    screen_id: str
    url_path: str | None = None
    title: str | None = None
    summary: str | None = None
    screen_type: str | None = None
    confidence: float = 0.0
    historical_match: float = 0.0


@dataclass(frozen=True, slots=True)
class RecipeStepMatchRequest:
    organization_id: UUID
    product_id: UUID
    session_id: UUID
    compiled_recipe: CompiledRecipe
    step_key: str
    current_screen: ScreenContext
    safe_actions: tuple[SafeActionContext, ...]
    candidate_screens: tuple[ScreenNodeContext, ...] = ()
    trace_id: str = ""


@dataclass(frozen=True, slots=True)
class RecipeStepMatchResult:
    matched: bool
    step_key: str
    screen_id: str | None
    screen_match_score: float
    action_id: str | None
    action_match_score: float
    confidence: float
    decision: Literal["matched", "possible_match", "not_found", "blocked_by_policy"]
    reason_codes: tuple[str, ...]
    evidence: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RecipeStepStatus:
    step_key: str
    status: ProgressStatus = "pending"
    attempt_count: int = 0
    matched_screen_id: str | None = None
    matched_action_id: str | None = None
    matched_confidence: float = 0.0
    failure_reason: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class RecipeProgressState:
    session_id: UUID
    recipe_id: UUID
    active_step_key: str | None
    step_statuses: dict[str, RecipeStepStatus]
    completed_count: int
    total_count: int
    progress_ratio: float
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class InitializeRecipeProgressRequest:
    organization_id: UUID
    session_id: UUID
    recipe_id: UUID
    compiled_recipe: CompiledRecipe


@dataclass(frozen=True, slots=True)
class StepProgressUpdateRequest:
    organization_id: UUID
    session_id: UUID
    recipe_id: UUID
    step_key: str
    status: ProgressStatus
    turn_id: str
    event_id: str
    matched_screen_id: str | None = None
    matched_action_id: str | None = None
    matched_confidence: float = 0.0
    failure_reason: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FallbackRequest:
    organization_id: UUID
    product_id: UUID
    session_id: UUID
    recipe_id: UUID
    step_key: str
    match_result: RecipeStepMatchResult
    current_screen: ScreenContext | None
    safe_actions: tuple[SafeActionContext, ...]
    progress_state: RecipeProgressState
    user_utterance: str | None = None
    trace_id: str = ""


@dataclass(frozen=True, slots=True)
class FallbackDecision:
    decision: Literal[
        "read_current_screen",
        "go_back",
        "safe_alternative_action",
        "ask_user",
        "explain_uncertainty",
        "skip_step",
        "enter_recovery",
    ]
    spoken_guidance: str
    browser_action_id: str | None
    reason_codes: tuple[str, ...]
    confidence: float
    should_update_progress: bool
    new_progress_status: str | None
