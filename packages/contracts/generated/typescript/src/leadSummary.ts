// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type InsightType = "pain_point" | "use_case" | "objection" | "buying_signal" | "question" | "feature_interest" | "persona" | "role" | "urgency" | "unanswered_question" | "decision_criteria" | "next_step";

export interface LeadInsight {
  insight_id: UuidString;
  insight_type: InsightType;
  value: string;
  confidence: number;
  evidence_transcript_event_ids: UuidString[];
  evidence_browser_action_ids: UuidString[];
  evidence_screen_ids: UuidString[];
  created_at: IsoDateTimeString;
}

export interface DemoSummary {
  duration_seconds: number;
  features_shown: string[];
  questions_asked: string[];
  screens_visited: UuidString[];
}

export interface Qualification {
  insights: LeadInsight[];
  urgency_level: string;
  confidence: number;
}

export interface CrmObject {
  object_type: string;
  properties: Metadata;
}

export interface CrmPayload {
  provider: string;
  objects: CrmObject[];
}

export interface LeadSummary {
  lead_summary_id: UuidString;
  session_id: UuidString;
  demo_summary: DemoSummary;
  qualification: Qualification;
  recommended_follow_up: string;
  crm_payload: CrmPayload;
  created_at: IsoDateTimeString;
}

export interface LeadInsightsResponse {
  items: LeadInsight[];
  next_cursor: string | null;
}

export interface LeadSummaryResponse {
  lead_summary: LeadSummary;
}

export interface CrmPayloadResponse {
  crm_payload: CrmPayload;
}

export interface FeatureShown {
  name: string;
  source: string;
  screen_id?: UuidString;
  action_event_id?: UuidString;
}

export interface FeaturesShownResponse {
  features: FeatureShown[];
  source: string;
  message: string;
}
