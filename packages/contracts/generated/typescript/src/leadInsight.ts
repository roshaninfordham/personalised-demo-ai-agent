// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type PostDemoInsightType = "pain_point" | "objection" | "buying_signal" | "role" | "urgency" | "feature_interest" | "unanswered_question" | "question" | "use_case" | "decision_criteria" | "next_step";

export interface EvidenceRefs {
  transcript_event_ids: UuidString[];
  browser_action_ids: UuidString[];
  screen_ids: UuidString[];
  recipe_step_ids: UuidString[];
}

export interface ExtractedLeadInsight {
  insight_type: PostDemoInsightType;
  content: string;
  confidence: number;
  importance: number;
  evidence: EvidenceRefs;
  source: string;
}
