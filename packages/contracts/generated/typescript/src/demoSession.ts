// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface DemoSession {
  session_id: UuidString;
  product_id: UuidString;
  start_url: string;
  status: SessionStatus;
  current_phase: DemoPhase;
  created_at: IsoDateTimeString;
  updated_at: IsoDateTimeString;
  product_name?: string;
  user_persona?: string;
  user_company?: string;
  user_display_name?: string;
  user_email?: string;
  recipe_id?: UuidString;
  browser_session_id?: string;
  transport_session_id?: string;
  started_at?: IsoDateTimeString;
  ended_at?: IsoDateTimeString;
}

export interface CreateDemoSessionRequest {
  product_id: UuidString;
  recipe_id?: UuidString;
  start_url?: string;
  user_persona?: string;
  user_company?: string;
  user_display_name?: string;
  user_email?: string;
}

export interface CreateDemoSessionResponse {
  session: DemoSession;
}

export interface StartDemoSessionRequest {
}

export interface StartDemoSessionResponse {
  session: DemoSession;
  join_config: JoinConfigResponse;
}

export interface EndDemoSessionRequest {
  reason?: string;
  force?: boolean;
}

export interface EndDemoSessionResponse {
  session: DemoSession;
}

export type DemoSessionResponse = DemoSession;

export interface ListDemoSessionsResponse {
  items: DemoSession[];
  next_cursor: string | null;
}

export interface SessionLiveState {
  available: boolean;
  current_screen: Metadata | null;
  safe_actions: Metadata[];
  browser_status: Metadata | null;
  latency: Metadata;
  live_state_status?: string;
}

export interface DemoSessionStateResponse {
  session: DemoSession;
  live_state: SessionLiveState;
}

export interface JoinConfigResponse {
  transport_provider: string;
  session_id: UuidString;
  room_id: string;
  join_token: string | null;
  expires_at: IsoDateTimeString;
  status: string;
}
