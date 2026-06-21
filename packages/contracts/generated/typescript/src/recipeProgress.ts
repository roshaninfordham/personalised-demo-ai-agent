// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface RecipeProgressEvent {
  session_id: UuidString;
  recipe_id: UuidString;
  step_key: string;
  status: string;
}
