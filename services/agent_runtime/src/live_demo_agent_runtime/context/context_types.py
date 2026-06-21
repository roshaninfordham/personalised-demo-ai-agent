"""Typed realtime-agent context objects."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ContextSource:
    source_id: str
    source_type: str
    confidence: float
    description: str


@dataclass(frozen=True, slots=True)
class ScreenContext:
    screen_id: str
    screen_hash: str
    url_path: str
    title: str | None
    summary: str
    confidence: float
    screenshot_artifact_id: str | None
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class SafeActionContext:
    action_id: str
    action_type: str
    label: str
    element_id: str | None
    risk_level: str
    score: float
    requires_confirmation: bool
    reason: str
    expires_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RecipeStepContext:
    step_key: str
    goal: str
    screen_hint: str | None = None
    click_hint: str | None = None
    talk_track: str | None = None
    allowed_actions: tuple[str, ...] = ()
    success_criteria: str | None = None
    fallback_strategy: str | None = None


@dataclass(frozen=True, slots=True)
class RecentTurnContext:
    speaker: str
    text: str
    chunk_type: str
    created_at: datetime | None
    turn_id: UUID | None
    transcript_event_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PersonaContext:
    likely_role: str | None = None
    role_confidence: float = 0.0
    interests: tuple[str, ...] = ()
    pain_points: tuple[str, ...] = ()
    objections: tuple[str, ...] = ()
    preferred_demo_direction: str | None = None
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProductSummaryContext:
    product_name: str
    product_url_domain: str
    summary: str
    confidence: float
    source: str


@dataclass(frozen=True, slots=True)
class KnowledgeFactContext:
    fact_id: str
    text: str
    score: float
    source: str


@dataclass(frozen=True, slots=True)
class SafetyRulesContext:
    never_click: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    high_risk_requires_confirmation: bool
    no_raw_js: bool = True
    no_raw_selector: bool = True
    claim_grounding_policy: str = "Only make product claims grounded in provided sources."


@dataclass(frozen=True, slots=True)
class ContextBudgetReport:
    max_tokens: int
    estimated_tokens: int
    truncated_sections: tuple[str, ...] = ()
    dropped_sections: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BuildRealtimeContextRequest:
    organization_id: UUID
    demo_session_id: UUID
    product_id: UUID
    user_utterance: str
    user_transcript_event_id: UUID | None
    active_turn_id: UUID
    trace_id: str
    include_retrieval: bool = True


@dataclass(frozen=True, slots=True)
class RealtimeAgentContext:
    organization_id: UUID
    demo_session_id: UUID
    product_id: UUID
    active_turn_id: UUID
    demo_phase: str
    user_utterance: str
    current_screen: ScreenContext | None
    safe_actions: tuple[SafeActionContext, ...]
    active_recipe_step: RecipeStepContext | None
    recent_turns: tuple[RecentTurnContext, ...]
    persona: PersonaContext
    product_summary: ProductSummaryContext | None
    retrieved_knowledge: tuple[KnowledgeFactContext, ...]
    safety_rules: SafetyRulesContext
    token_budget_report: ContextBudgetReport
    source_map: tuple[ContextSource, ...] = field(default_factory=tuple)
