// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface FeatureShownRecord {
  feature_shown_id: UuidString;
  feature_key: string;
  feature_label: string;
  feature_category?: string | null;
  confidence: number;
  source_type: string;
  evidence: FeatureEvidenceRefs;
}

export interface FeatureEvidenceRefs {
  transcript_event_ids: UuidString[];
  browser_action_ids: UuidString[];
  screen_ids: UuidString[];
  recipe_step_ids: UuidString[];
}

export interface FeatureShownRecordsResponse {
  items: FeatureShownRecord[];
}
