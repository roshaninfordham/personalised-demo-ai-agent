import type { BoundingBox, BrowserActionType, RiskLevel } from "@live-demo-agent/contracts";

import type { InternalElement } from "../screen/elementExtractor.js";
import { actionId } from "../screen/screenHasher.js";

export type SafeActionInternal = {
  action_id: string;
  action_type: BrowserActionType;
  element_id: string;
  label: string;
  risk_level: RiskLevel;
  score: number;
  requires_confirmation: boolean;
  reason: string;
  expires_at: string;
  screen_hash: string;
  bbox?: BoundingBox;
};

export type RecipeStepRankingContext = {
  step_key: string;
  goal?: string;
  click_hint?: string | null;
  screen_hint?: string | null;
};

export type ActionRankingRequest = {
  user_intent: string;
  actions: SafeActionInternal[];
  active_recipe_step?: RecipeStepRankingContext | null;
  historical_success?: Record<string, number>;
  latency_cost_ms?: Record<string, number>;
  top_k?: number;
  execution_threshold?: number;
};

export type RankedAction = SafeActionInternal & {
  execution_score: number;
  executable: boolean;
  components: {
    user_intent_match: number;
    recipe_step_match: number;
    element_label_match: number;
    visibility_score: number;
    historical_success: number;
    demo_value: number;
    risk_score: number;
    latency_cost: number;
  };
};

export const ACTION_EXECUTION_SCORE_THRESHOLD = 0.72;

export function generateSafeActions(
  elements: InternalElement[],
  screenHash: string,
  threshold: number,
): SafeActionInternal[] {
  const expiresAt = new Date(Date.now() + 5 * 60 * 1000).toISOString();
  return elements
    .filter((element) => element.visible && element.enabled && element.risk_level !== "blocked")
    .map((element) => {
      const actionType: BrowserActionType = ["input", "textarea", "select"].includes(element.role)
        ? "type_into_element"
        : "click_element";
      const riskPenalty =
        element.risk_level === "high" ? 0.4 : element.risk_level === "medium" ? 0.2 : 0;
      const score = Math.max(0, Math.min(1, 0.9 - riskPenalty));
      return {
        action_id: actionId(actionType, element.element_id),
        action_type: actionType,
        element_id: element.element_id,
        label: element.label,
        risk_level: element.risk_level,
        score,
        requires_confirmation: element.risk_level === "high",
        reason: `${element.role} '${element.label}' classified as ${element.risk_level}.`,
        expires_at: expiresAt,
        screen_hash: screenHash,
        bbox: element.bbox,
      };
    })
    .filter((action) => action.score >= threshold || action.risk_level === "low")
    .slice(0, 20);
}

export function rankActionsForIntent(request: ActionRankingRequest): {
  ranked_actions: RankedAction[];
  top_executable_action: RankedAction | null;
} {
  const threshold = request.execution_threshold ?? ACTION_EXECUTION_SCORE_THRESHOLD;
  const ranked = request.actions
    .map((action) => scoreAction(action, request, threshold))
    .sort(compareRankedActions)
    .slice(0, request.top_k ?? 8);
  return {
    ranked_actions: ranked,
    top_executable_action: ranked.find((action) => action.executable) ?? null,
  };
}

function scoreAction(
  action: SafeActionInternal,
  request: ActionRankingRequest,
  threshold: number,
): RankedAction {
  const userTokens = tokenize(request.user_intent);
  const labelTokens = tokenize(`${action.label} ${action.reason} ${action.action_type}`);
  const recipeTokens = tokenize(
    [
      request.active_recipe_step?.goal,
      request.active_recipe_step?.click_hint,
      request.active_recipe_step?.screen_hint,
    ].join(" "),
  );
  const userIntentMatch = Math.max(
    coverage(userTokens, labelTokens),
    importantTokenOverlap(userTokens, labelTokens),
  );
  const recipeStepMatch = recipeTokens.size === 0 ? 0 : coverage(recipeTokens, labelTokens);
  const elementLabelMatch = exactPhraseMatch(request.user_intent, action.label);
  const visibilityScore = clamp01(action.score);
  const historicalSuccess = clamp01(request.historical_success?.[action.action_id] ?? 0.5);
  const demoValue = demoValueFor(action);
  const riskScore = riskScoreFor(action.risk_level, action.requires_confirmation);
  const latencyCost = latencyCostFor(request.latency_cost_ms?.[action.action_id] ?? 0);
  const executionScore = clamp01(
    0.3 * userIntentMatch +
      0.25 * recipeStepMatch +
      0.15 * elementLabelMatch +
      0.1 * visibilityScore +
      0.1 * historicalSuccess +
      0.1 * demoValue -
      0.35 * riskScore -
      0.1 * latencyCost,
  );
  const executable =
    executionScore >= threshold && action.risk_level !== "blocked" && !action.requires_confirmation;
  return {
    ...action,
    execution_score: executionScore,
    executable,
    components: {
      user_intent_match: userIntentMatch,
      recipe_step_match: recipeStepMatch,
      element_label_match: elementLabelMatch,
      visibility_score: visibilityScore,
      historical_success: historicalSuccess,
      demo_value: demoValue,
      risk_score: riskScore,
      latency_cost: latencyCost,
    },
  };
}

function compareRankedActions(left: RankedAction, right: RankedAction): number {
  return (
    right.execution_score - left.execution_score ||
    riskScoreFor(left.risk_level, left.requires_confirmation) -
      riskScoreFor(right.risk_level, right.requires_confirmation) ||
    left.label.localeCompare(right.label) ||
    left.action_id.localeCompare(right.action_id)
  );
}

function tokenize(text: string): Set<string> {
  return new Set(
    text
      .normalize("NFKC")
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .split(/\s+/)
      .filter((token) => token.length > 1 && !STOPWORDS.has(token)),
  );
}

function jaccard(left: Set<string>, right: Set<string>): number {
  if (left.size === 0 || right.size === 0) {
    return 0;
  }
  let intersection = 0;
  for (const token of left) {
    if (right.has(token)) {
      intersection += 1;
    }
  }
  return intersection / (left.size + right.size - intersection);
}

function coverage(query: Set<string>, candidate: Set<string>): number {
  if (query.size === 0 || candidate.size === 0) {
    return 0;
  }
  let matched = 0;
  for (const token of query) {
    if (candidate.has(token)) {
      matched += 1;
    }
  }
  return matched / query.size;
}

function exactPhraseMatch(intent: string, label: string): number {
  const normalizedIntent = normalize(intent);
  const normalizedLabel = normalize(label);
  if (normalizedIntent.includes(normalizedLabel) || normalizedLabel.includes(normalizedIntent)) {
    return 1;
  }
  const intentTokens = tokenize(intent);
  const labelTokens = tokenize(label);
  return Math.max(
    jaccard(intentTokens, labelTokens),
    importantTokenOverlap(intentTokens, labelTokens),
  );
}

function importantTokenOverlap(left: Set<string>, right: Set<string>): number {
  for (const token of left) {
    if (IMPORTANT_ACTION_TOKENS.has(token) && right.has(token)) {
      return 1;
    }
  }
  return 0;
}

function demoValueFor(action: SafeActionInternal): number {
  const label = normalize(action.label);
  if (/(dashboard|reports|analytics|metric|create|add)/.test(label)) {
    return 1;
  }
  if (/(filter|search|overview|highlight|read)/.test(label)) {
    return 0.75;
  }
  return 0.45;
}

function riskScoreFor(riskLevel: RiskLevel, requiresConfirmation: boolean): number {
  if (riskLevel === "blocked") {
    return 1;
  }
  if (riskLevel === "high" || requiresConfirmation) {
    return 0.8;
  }
  if (riskLevel === "medium") {
    return 0.35;
  }
  return 0.05;
}

function latencyCostFor(latencyMs: number): number {
  if (latencyMs <= 0) {
    return 0;
  }
  return clamp01(latencyMs / 2_000);
}

function normalize(text: string): string {
  return text
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

const STOPWORDS = new Set([
  "the",
  "this",
  "that",
  "can",
  "you",
  "me",
  "how",
  "do",
  "i",
  "to",
  "a",
  "an",
  "of",
  "and",
  "or",
  "please",
  "show",
  "see",
  "continue",
]);

const IMPORTANT_ACTION_TOKENS = new Set([
  "add",
  "analytics",
  "create",
  "dashboard",
  "export",
  "metric",
  "metrics",
  "overview",
  "report",
  "reports",
]);
