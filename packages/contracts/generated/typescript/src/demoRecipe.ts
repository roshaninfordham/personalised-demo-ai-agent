// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export type RecipeStatus = "draft" | "active" | "archived";

export type RecipeProgressStatus = "pending" | "in_progress" | "completed" | "skipped" | "failed" | "adapted" | "blocked";

export type RecipeDemoPhase = "START" | "DISCOVERY" | "OVERVIEW" | "CORE_WORKFLOW" | "DEEP_DIVE" | "Q_AND_A" | "SUMMARY" | "END" | "RECOVERY";

export interface RecipeValidationIssue {
  path: string;
  code: string;
  message: string;
  severity: "error" | "warning";
}

export interface AllowedFormFieldInput {
  field_label_pattern: string;
  field_type: string;
  max_chars: number;
}

export interface ConfirmationRequiredActionInput {
  action_type: string;
  label_pattern: string;
  reason: string;
}

export interface DemoStep {
  step_id: UuidString;
  step_order: number;
  step_key: string;
  goal: string;
  phase?: RecipeDemoPhase;
  screen_hint?: string;
  click_hint?: string;
  talk_track?: string;
  allowed_actions?: string[];
  success_criteria?: string[];
  fallback_strategy?: string;
  max_attempts?: number;
  required?: boolean;
  confidence?: number;
  source_references?: string[];
}

export interface DemoStepInput {
  step_order: number;
  step_key: string;
  goal: string;
  phase?: RecipeDemoPhase;
  screen_hint?: string;
  click_hint?: string;
  talk_track?: string;
  allowed_actions?: string[];
  success_criteria?: string[];
  fallback_strategy?: string;
  max_attempts?: number;
  required?: boolean;
  confidence?: number;
  source_references?: string[];
}

export interface CreateDemoRecipeRequest {
  recipe_name: string;
  target_persona?: string;
  demo_goal: string;
  never_click?: string[];
  allowed_domains?: string[];
  allowed_form_fields?: AllowedFormFieldInput[];
  confirmation_required_actions?: ConfirmationRequiredActionInput[];
  global_talk_track?: string;
  steps: DemoStepInput[];
}

export interface UpdateDemoRecipeRequest {
  recipe_name?: string;
  target_persona?: string;
  demo_goal?: string;
  never_click?: string[];
  allowed_domains?: string[];
  allowed_form_fields?: AllowedFormFieldInput[];
  confirmation_required_actions?: ConfirmationRequiredActionInput[];
  global_talk_track?: string;
  steps?: DemoStepInput[];
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

export interface ValidateDemoRecipeRequest {
  recipe: Record<string, JsonValue>;
}

export interface ValidateDemoRecipeResponse {
  valid: boolean;
  errors: RecipeValidationIssue[];
  warnings: RecipeValidationIssue[];
  normalized_recipe?: CreateDemoRecipeRequest | null;
}

export interface GenerateDemoRecipeRequest {
  target_persona?: string;
  text_guidance: string;
}

export interface GenerateDemoRecipeResponse {
  recipe: CreateDemoRecipeRequest;
  validation: ValidateDemoRecipeResponse;
  generation_run_id: UuidString;
  recipe_id?: UuidString | null;
  status: string;
}

export interface CompiledDemoRecipeResponse {
  compiled_recipe_id: UuidString;
  recipe_id: UuidString;
  recipe_hash: string;
  compiled_hash: string;
  compiled_payload: Record<string, JsonValue>;
  status: string;
}

export interface RecipeStepProgressResponse {
  step_key: string;
  status: RecipeProgressStatus;
  attempt_count: number;
  matched_screen_id?: string;
  matched_action_id?: string;
  matched_confidence: number;
  failure_reason?: string;
  evidence?: Record<string, JsonValue>;
}

export interface RecipeProgressResponse {
  session_id: UuidString;
  recipe_id: UuidString;
  active_step_key: string | null;
  steps: RecipeStepProgressResponse[];
  completed_count: number;
  total_count: number;
  progress_ratio: number;
}

export interface ActivateDemoRecipeResponse {
  recipe: DemoRecipe;
}

export interface ListDemoRecipesResponse {
  items: DemoRecipe[];
  next_cursor: string | null;
}
