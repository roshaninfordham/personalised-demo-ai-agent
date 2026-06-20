// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface DemoStep {
  step_id: UuidString;
  step_order: number;
  step_key: string;
  goal: string;
  screen_hint?: string;
  click_hint?: string;
  talk_track?: string;
  allowed_actions?: string[];
  success_criteria?: string[];
  fallback_strategy?: string;
}

export interface DemoRecipe {
  recipe_id: UuidString;
  product_id: UuidString;
  recipe_name: string;
  demo_goal: string;
  steps: DemoStep[];
  never_click: string[];
  created_at: IsoDateTimeString;
  updated_at: IsoDateTimeString;
}

export interface RecipeValidationResult {
  valid: boolean;
  errors: string[];
}
