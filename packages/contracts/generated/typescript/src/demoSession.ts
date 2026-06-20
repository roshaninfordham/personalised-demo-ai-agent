// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface DemoSession {
  session_id: UuidString;
  product_id: UuidString;
  product_url: string;
  status: SessionStatus;
  current_phase: DemoPhase;
  created_at: IsoDateTimeString;
  updated_at: IsoDateTimeString;
  product_name?: string;
  target_persona?: string;
  recipe_id?: UuidString;
  browser_session_id?: string;
  transport_session_id?: string;
  started_at?: IsoDateTimeString;
  ended_at?: IsoDateTimeString;
}

export interface CreateDemoSessionRequest {
  product_url: string;
  product_name?: string;
  target_persona?: string;
  positioning?: string;
  demo_goals?: string[];
  what_to_show?: string[];
  what_to_avoid?: string[];
  recipe_id?: UuidString;
  metadata?: Metadata;
}

export interface CreateDemoSessionResponse {
  session: DemoSession;
}

export interface StartDemoSessionRequest {
  session_id: UuidString;
}

export interface StartDemoSessionResponse {
  session: DemoSession;
}

export interface EndDemoSessionRequest {
  session_id: UuidString;
  reason?: string;
}

export interface EndDemoSessionResponse {
  session: DemoSession;
}
