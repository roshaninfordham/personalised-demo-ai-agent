// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type RecipeStatus = "draft" | "active" | "archived";

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

export interface DemoStepInput {
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
  target_persona?: string;
  demo_goal: string;
  status: RecipeStatus;
  is_active: boolean;
  steps: DemoStep[];
  never_click: string[];
  global_talk_track?: string;
  created_at: IsoDateTimeString;
  updated_at: IsoDateTimeString;
}

export interface CreateDemoRecipeRequest {
  recipe_name: string;
  target_persona?: string;
  demo_goal: string;
  never_click?: string[];
  global_talk_track?: string;
  steps: DemoStepInput[];
}

export interface UpdateDemoRecipeRequest {
  recipe_name?: string;
  target_persona?: string;
  demo_goal?: string;
  never_click?: string[];
  global_talk_track?: string;
  steps?: DemoStepInput[];
}

export type DemoRecipeResponse = DemoRecipe;

export interface ListDemoRecipesResponse {
  items: DemoRecipe[];
  next_cursor: string | null;
}

export interface RecipeValidationIssue {
  path: string;
  code: string;
  message: string;
}

export interface RecipeValidationResult {
  valid: boolean;
  errors: string[];
}

export interface ValidateDemoRecipeResponse {
  valid: boolean;
  errors: RecipeValidationIssue[];
  warnings: RecipeValidationIssue[];
}

export interface ActivateDemoRecipeResponse {
  recipe: DemoRecipe;
}
