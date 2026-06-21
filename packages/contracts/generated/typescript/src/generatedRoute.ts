// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface GeneratedDemoRoute {
  route_id: string;
  route_name: string;
  route_type: "generated" | "manual" | "hybrid";
  status: "draft" | "active" | "archived" | "invalid";
  confidence: number;
  summary?: string | null;
  steps: Record<string, never>[];
}
