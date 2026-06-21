// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface ProductLearningRun {
  learning_run_id: string;
  organization_id: string;
  product_id: string;
  session_id?: string | null;
  start_url: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled" | "dead_letter";
  trigger_type: "product_created" | "session_created" | "manual" | "recipe_missing" | "screen_unknown" | "scheduled_refresh";
  attempt_count: number;
  max_attempts: number;
  error_code?: string | null;
  metrics?: Record<string, JsonValue>;
  created_at: string;
  updated_at: string;
}
