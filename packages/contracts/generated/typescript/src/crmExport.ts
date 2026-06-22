// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type CrmExportStatus = "pending" | "validated" | "sent" | "failed" | "skipped" | "dry_run_completed";

export interface CrmExportRecord {
  crm_export_id: UuidString;
  provider: string;
  status: CrmExportStatus;
  dry_run: boolean;
  external_object_ids: Metadata;
  created_at: IsoDateTimeString;
}

export interface CrmExportsResponse {
  items: CrmExportRecord[];
}
