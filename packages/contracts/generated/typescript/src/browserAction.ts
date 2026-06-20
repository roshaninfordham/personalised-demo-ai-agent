// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type BrowserActionType = "read_current_screen" | "highlight_element" | "click_element" | "type_into_element" | "type_demo_text" | "scroll" | "go_back" | "navigate_to_allowed_url" | "wait_for_idle" | "take_screenshot";

export type ScrollDirection = "up" | "down" | "left" | "right";

export interface BrowserActionCommand {
  command_id: UuidString;
  session_id: UuidString;
  browser_session_id: string;
  action_type: BrowserActionType;
  created_at: IsoDateTimeString;
  element_id?: string;
  text?: string;
  direction?: ScrollDirection;
  url?: string;
  requires_cursor_animation?: boolean;
  policy_context?: Metadata;
}

export interface BrowserActionResult {
  browser_action_id?: UuidString;
  command_id: UuidString;
  session_id: UuidString;
  success: boolean;
  policy_decision: PolicyDecision;
  risk_level: RiskLevel;
  latency_ms: number;
  created_at: IsoDateTimeString;
  from_screen_id?: UuidString;
  to_screen_id?: UuidString;
  new_screen_summary?: string;
  error_code?: string;
  error_message?: string;
}

export interface SafeAction {
  action_id: UuidString;
  action_type: BrowserActionType;
  label: string;
  element_id?: string;
  risk_level: RiskLevel;
  policy_decision: PolicyDecision;
  confidence: number;
  reason?: string;
}

export interface CursorMoveEventPayload {
  x: number;
  y: number;
  duration_ms: number;
}

export interface ElementHighlightEventPayload {
  element_id: string;
  duration_ms?: number;
}
