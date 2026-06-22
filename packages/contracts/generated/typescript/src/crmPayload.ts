// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface GenericCrmPayload {
  schema_version: string;
  session_id: UuidString;
  product_id: UuidString;
  lead: Metadata;
  demo: Metadata;
  qualification: Metadata;
  recommended_follow_up: Metadata;
  evidence: Metadata;
  metadata: Metadata;
}
