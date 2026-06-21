// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type CompiledRecipeStatus = "active" | "stale" | "invalid" | "archived";

export interface CompiledRecipeArtifact {
  recipe_id: UuidString;
  recipe_hash: string;
  compiled_hash: string;
  compiled_payload: Record<string, JsonValue>;
  status: CompiledRecipeStatus;
}
