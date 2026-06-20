// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type TranscriptSpeaker = "user" | "assistant" | "system" | "tool";

export type TranscriptChunkType = "partial" | "final" | "interrupted";

export interface TranscriptEvent {
  transcript_event_id: UuidString;
  session_id: UuidString;
  speaker: TranscriptSpeaker;
  chunk_type: TranscriptChunkType;
  text: string;
  created_at: IsoDateTimeString;
  start_ms?: number;
  end_ms?: number;
  confidence?: number;
  turn_id?: string;
}

export interface TranscriptEventsResponse {
  items: TranscriptEvent[];
  next_cursor: string | null;
}

export interface QuestionResponse {
  text: string;
  source: string;
  transcript_event_id?: UuidString;
  insight_id?: UuidString;
  created_at: IsoDateTimeString;
}

export interface QuestionsResponse {
  items: QuestionResponse[];
  next_cursor: string | null;
}
