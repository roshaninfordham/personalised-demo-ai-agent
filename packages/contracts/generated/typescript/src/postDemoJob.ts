// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type PostDemoJobType = "extract_lead_insights" | "track_features_shown" | "generate_lead_summary" | "export_crm_payload" | "run_full_post_demo_intelligence";

export interface PostDemoRunRequest {
  run_mode?: string;
  export_crm?: boolean;
  crm_provider?: string;
}

export interface PostDemoRunResponse {
  session_id: UuidString;
  status: string;
  lead_summary_id: UuidString | null;
  crm_export_id: UuidString | null;
}
