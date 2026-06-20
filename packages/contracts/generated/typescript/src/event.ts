// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type EventType = "session.created" | "session.prewarming.started" | "session.started" | "session.ended" | "browser.session.created" | "browser.navigation.started" | "browser.navigation.completed" | "browser.screen.updated" | "browser.cursor.move" | "browser.cursor.click" | "browser.element.highlight" | "browser.action.started" | "browser.action.completed" | "browser.action.failed" | "agent.greeting.started" | "agent.turn.started" | "agent.turn.completed" | "agent.interrupted" | "transcript.partial" | "transcript.final" | "learner.started" | "learner.screen_summary.ready" | "learner.demo_graph.updated" | "lead_summary.ready" | "artifact.created" | "artifact.deleted" | "error";

export interface EventEnvelope {
  event_id: UuidString;
  session_id: UuidString | null;
  organization_id: UuidString | null;
  event_type: EventType;
  created_at: IsoDateTimeString;
  trace_id: TraceId;
  payload: Metadata;
}
