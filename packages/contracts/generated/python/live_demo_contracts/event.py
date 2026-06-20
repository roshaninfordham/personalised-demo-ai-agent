# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: F401

from __future__ import annotations

from enum import StrEnum

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
    ERROR = "error"


class EventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UuidString
    session_id: UuidString
    event_type: EventType
    created_at: IsoDateTimeString
    trace_id: TraceId
    payload: Metadata
