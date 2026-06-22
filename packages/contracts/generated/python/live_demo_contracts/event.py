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
    SESSION_PREWARMING_COMPLETED = "session.prewarming.completed"
    SESSION_PREWARMING_DEGRADED = "session.prewarming.degraded"
    SESSION_PREWARMING_FAILED = "session.prewarming.failed"
    SESSION_RESOURCE_ALLOCATING = "session.resource.allocating"
    SESSION_RESOURCE_READY = "session.resource.ready"
    SESSION_RESOURCE_FAILED = "session.resource.failed"
    SESSION_RESOURCE_RELEASING = "session.resource.releasing"
    SESSION_RESOURCE_RELEASED = "session.resource.released"
    SESSION_RESOURCE_RELEASE_FAILED = "session.resource.release_failed"
    SESSION_READINESS_UPDATED = "session.readiness.updated"
    SESSION_WAITING_FOR_USER = "session.waiting_for_user"
    SESSION_LIVE_STARTING = "session.live.starting"
    SESSION_LIVE_STARTED = "session.live.started"
    SESSION_LIVE_DEGRADED = "session.live.degraded"
    SESSION_SYNC_ACTION_QUEUED = "session.sync.action_queued"
    SESSION_SYNC_ACTION_STARTED = "session.sync.action_started"
    SESSION_SYNC_SCREEN_UPDATED = "session.sync.screen_updated"
    SESSION_SYNC_TIMEOUT = "session.sync.timeout"
    SESSION_RECOVERY_STARTED = "session.recovery.started"
    SESSION_RECOVERY_SCREEN_READ = "session.recovery.screen_read"
    SESSION_RECOVERY_GO_BACK_ATTEMPTED = "session.recovery.go_back_attempted"
    SESSION_RECOVERY_HOME_NAVIGATION_ATTEMPTED = "session.recovery.home_navigation_attempted"
    SESSION_RECOVERY_RESOLVED = "session.recovery.resolved"
    SESSION_RECOVERY_NEEDS_USER = "session.recovery.needs_user"
    SESSION_RECOVERY_FAILED = "session.recovery.failed"
    SESSION_ENDING = "session.ending"
    SESSION_FINALIZING = "session.finalizing"
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    SESSION_COMPLETED_WITH_WARNINGS = "session.completed_with_warnings"
    SESSION_FAILED = "session.failed"
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
    POST_DEMO_STARTED = "post_demo.started"
    POST_DEMO_COMPLETED = "post_demo.completed"
    POST_DEMO_FAILED = "post_demo.failed"
    LEAD_INSIGHTS_EXTRACTED = "lead_insights.extracted"
    LEAD_INSIGHT_CREATED = "lead_insight.created"
    LEAD_INSIGHT_UPDATED = "lead_insight.updated"
    FEATURES_SHOWN_TRACKED = "features_shown.tracked"
    FEATURE_SHOWN_CREATED = "feature_shown.created"
    LEAD_SUMMARY_GENERATION_STARTED = "lead_summary.generation.started"
    LEAD_SUMMARY_READY = "lead_summary.ready"
    LEAD_SUMMARY_FAILED = "lead_summary.failed"
    CRM_EXPORT_REQUESTED = "crm_export.requested"
    CRM_EXPORT_VALIDATED = "crm_export.validated"
    CRM_EXPORT_DRY_RUN_COMPLETED = "crm_export.dry_run_completed"
    CRM_EXPORT_SENT = "crm_export.sent"
    CRM_EXPORT_FAILED = "crm_export.failed"
    CRM_EXPORT_SKIPPED = "crm_export.skipped"
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
