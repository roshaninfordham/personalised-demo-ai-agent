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


class EventType(StrEnum):
    SESSION_CREATED = "session.created"
    SESSION_PREWARMING_STARTED = "session.prewarming.started"
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    PRODUCT_GUIDANCE_CREATED = "product_guidance.created"
    PRODUCT_GUIDANCE_UPDATED = "product_guidance.updated"
    PRODUCT_GUIDANCE_DELETED = "product_guidance.deleted"
    DEMO_RECIPE_CREATED = "demo_recipe.created"
    DEMO_RECIPE_UPDATED = "demo_recipe.updated"
    DEMO_RECIPE_DELETED = "demo_recipe.deleted"
    DEMO_RECIPE_ACTIVATED = "demo_recipe.activated"
    DEMO_RECIPE_ARCHIVED = "demo_recipe.archived"
    RECIPE_VALIDATION_COMPLETED = "recipe.validation.completed"
    RECIPE_VALIDATION_FAILED = "recipe.validation.failed"
    RECIPE_GENERATION_STARTED = "recipe.generation.started"
    RECIPE_GENERATION_COMPLETED = "recipe.generation.completed"
    RECIPE_GENERATION_FAILED = "recipe.generation.failed"
    RECIPE_COMPILED = "recipe.compiled"
    RECIPE_COMPILATION_FAILED = "recipe.compilation.failed"
    RECIPE_MATCH_COMPLETED = "recipe.match.completed"
    RECIPE_MATCH_FAILED = "recipe.match.failed"
    RECIPE_PROGRESS_INITIALIZED = "recipe.progress.initialized"
    RECIPE_STEP_STARTED = "recipe.step.started"
    RECIPE_STEP_IN_PROGRESS = "recipe.step.in_progress"
    RECIPE_STEP_COMPLETED = "recipe.step.completed"
    RECIPE_STEP_SKIPPED = "recipe.step.skipped"
    RECIPE_STEP_FAILED = "recipe.step.failed"
    RECIPE_STEP_ADAPTED = "recipe.step.adapted"
    RECIPE_STEP_BLOCKED = "recipe.step.blocked"
    RECIPE_FALLBACK_USED = "recipe.fallback.used"
    BROWSER_SESSION_CREATED = "browser.session.created"
    BROWSER_NAVIGATION_STARTED = "browser.navigation.started"
    BROWSER_NAVIGATION_COMPLETED = "browser.navigation.completed"
    BROWSER_SCREEN_UPDATED = "browser.screen.updated"
    BROWSER_CURSOR_MOVE = "browser.cursor.move"
    BROWSER_CURSOR_CLICK = "browser.cursor.click"
    BROWSER_ELEMENT_HIGHLIGHT = "browser.element.highlight"
    BROWSER_ACTION_STARTED = "browser.action.started"
    BROWSER_ACTION_COMPLETED = "browser.action.completed"
    BROWSER_ACTION_FAILED = "browser.action.failed"
    AGENT_GREETING_STARTED = "agent.greeting.started"
    AGENT_TURN_STARTED = "agent.turn.started"
    AGENT_TURN_COMPLETED = "agent.turn.completed"
    AGENT_INTERRUPTED = "agent.interrupted"
    TRANSCRIPT_PARTIAL = "transcript.partial"
    TRANSCRIPT_FINAL = "transcript.final"
    LEARNER_STARTED = "learner.started"
    LEARNER_SCREEN_SUMMARY_READY = "learner.screen_summary.ready"
    LEARNER_DEMO_GRAPH_UPDATED = "learner.demo_graph.updated"
    LEAD_SUMMARY_READY = "lead_summary.ready"
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_DELETED = "artifact.deleted"
    ERROR = "error"


class EventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UuidString
    session_id: UuidString | None
    organization_id: UuidString | None
    event_type: EventType
    created_at: IsoDateTimeString
    trace_id: TraceId
    payload: Metadata
