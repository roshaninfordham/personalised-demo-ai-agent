// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface RecipeMatchResult {
  matched: boolean;
  step_key: string;
  screen_id?: string;
  action_id?: string;
  confidence: number;
  decision: string;
  reason_codes: string[];
}
