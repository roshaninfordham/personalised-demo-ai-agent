// Generated from packages/contracts/schemas. Do not edit manually.

export type UuidString = string;

export type IsoDateTimeString = string;

export type TraceId = string;

export type ProviderName = string;

export type JsonValue = string | number | number | boolean | null;

export type Metadata = Record<string, JsonValue>;

export type RiskLevel = "low" | "medium" | "high" | "blocked" | "unknown";

export type PolicyDecision = "allowed" | "blocked" | "confirmation_required";

export type DemoPhase = "created" | "prewarming" | "discovery" | "overview" | "core_workflow" | "deep_dive" | "q_and_a" | "summary" | "recovery" | "completed" | "failed";

export type SessionStatus = "created" | "prewarming" | "waiting_for_user" | "live" | "ending" | "completed" | "failed";

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}
