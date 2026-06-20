// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type ElementRole = "button" | "link" | "input" | "textarea" | "select" | "checkbox" | "radio" | "navigation" | "tab" | "table" | "chart" | "card" | "modal" | "text" | "unknown";

export interface UIElement {
  element_id: string;
  role: ElementRole;
  label: string;
  bbox: BoundingBox;
  visible: boolean;
  enabled: boolean;
  risk_level: RiskLevel;
  confidence: number;
}

export interface ScreenSummary {
  screen_id: UuidString;
  summary: string;
  confidence: number;
  created_at: IsoDateTimeString;
}

export interface ScreenState {
  screen_id: UuidString;
  session_id: UuidString;
  browser_session_id: string;
  url: string;
  title: string;
  screen_hash: string;
  visible_text: string[];
  summary: ScreenSummary;
  elements: UIElement[];
  screenshot_uri: string;
  confidence: number;
  created_at: IsoDateTimeString;
}
