import { containsPhrase } from "./actionPolicy.js";

export type CompiledRecipePolicy = {
  allowedActions: { actionType: string; labelPattern: string; riskLevelMax: string }[];
  neverClick: string[];
  allowedDomains: string[];
  allowedFormFields: { fieldLabelPattern: string; fieldType: string; maxChars: number }[];
  confirmationRequiredActions: { actionType: string; labelPattern: string; reason: string }[];
};

export function compileRecipePolicy(raw: Record<string, unknown> | null): CompiledRecipePolicy {
  const source = raw ?? {};
  return {
    allowedActions: objects(source.allowed_actions).slice(0, 100).map((item) => ({
      actionType: stringValue(item.action_type),
      labelPattern: stringValue(item.label_pattern),
      riskLevelMax: stringValue(item.risk_level_max, "medium"),
    })),
    neverClick: strings(source.never_click).slice(0, 100),
    allowedDomains: strings(source.allowed_domains).slice(0, 50),
    allowedFormFields: objects(source.allowed_form_fields).slice(0, 100).map((item) => ({
      fieldLabelPattern: stringValue(item.field_label_pattern),
      fieldType: stringValue(item.field_type, "text"),
      maxChars: Number(item.max_chars ?? 120),
    })),
    confirmationRequiredActions: objects(source.confirmation_required_actions)
      .slice(0, 100)
      .map((item) => ({
        actionType: stringValue(item.action_type),
        labelPattern: stringValue(item.label_pattern),
        reason: stringValue(item.reason),
      })),
  };
}

export function recipeRequiresConfirmation(
  policy: CompiledRecipePolicy,
  actionType: string,
  label: string,
): boolean {
  return policy.confirmationRequiredActions.some(
    (pattern) => pattern.actionType === actionType && containsPhrase(label, [pattern.labelPattern]),
  );
}

function objects(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null && !Array.isArray(item))
    : [];
}

function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function stringValue(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}
