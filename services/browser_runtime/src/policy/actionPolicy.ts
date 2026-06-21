import { actionSafetyRules } from "@live-demo-agent/policies";

export type PolicyDecisionValue = "allowed" | "blocked" | "confirmation_required" | "not_applicable";
export type PolicyRiskLevel = "low" | "medium" | "high" | "blocked" | "unknown";

export type PolicyActor = {
  actor_type: "user" | "agent" | "system" | "service";
  actor_id: string | null;
  role: string;
};

export type ActionPolicyRequest = {
  organization_id: string;
  session_id?: string | null;
  actor: PolicyActor;
  action_type: string;
  action_label?: string | null;
  element_role?: string | null;
  element_label?: string | null;
  element_text?: string | null;
  surrounding_text?: string | null;
  input_type?: string | null;
  current_url?: string | null;
  target_url?: string | null;
  allowed_domains?: string[];
  recipe_never_click?: string[];
  confirmation?: { confirmed: boolean } | null;
  trace_id: string;
};

export type PolicyDecision = {
  decision_id: string;
  decision: PolicyDecisionValue;
  risk_level: PolicyRiskLevel;
  risk_score: number;
  requires_confirmation: boolean;
  reason_codes: string[];
  matched_rules: { rule_id: string; category: string; phrase?: string }[];
  actor: PolicyActor;
  organization_id: string;
  session_id: string | null;
  trace_id: string;
  created_at: string;
};

export class DeterministicActionSafetyPolicy {
  evaluate(request: ActionPolicyRequest): PolicyDecision {
    const rawCombined = [
      request.action_type,
      request.action_label ?? "",
      request.element_role ?? "",
      request.element_label ?? "",
      request.element_text ?? "",
      request.surrounding_text ?? "",
      request.input_type ?? "",
      request.target_url ?? "",
    ].join(" ");
    const rawLower = rawCombined.toLowerCase();
    const combined = normalizePolicyText(rawCombined);
    const forbidden = actionSafetyRules.forbidden_authority;
    if (forbidden.javascript_markers.some((marker) => rawLower.includes(marker.toLowerCase()))) {
      return decision(request, "blocked", "blocked", 1, ["javascript_forbidden"]);
    }
    if (forbidden.selector_markers.some((marker) => rawLower.includes(marker.toLowerCase()))) {
      return decision(request, "blocked", "blocked", 1, ["raw_selector_forbidden"]);
    }
    if (containsPhrase(combined, request.recipe_never_click ?? [])) {
      return decision(request, "blocked", "blocked", 1, ["recipe_never_click_match"]);
    }
    const matches = actionSafetyRules.categories.filter((category) =>
      containsPhrase(combined, [...category.phrases]),
    );
    if (matches.some((match) => match.category === "blocked_destructive")) {
      return decision(request, "blocked", "blocked", 1, ["blocked_destructive_action"], matches);
    }
    if (matches.some((match) => match.category === "payment_billing")) {
      return decision(request, "blocked", "blocked", 1, ["payment_billing_blocked"], matches);
    }
    if (request.target_url && !domainAllowed(request.target_url, request.allowed_domains ?? [])) {
      return decision(request, "blocked", "blocked", 1, ["domain_not_allowed"], matches);
    }
    if (isSensitiveField(request)) {
      return decision(request, "blocked", "blocked", 1, ["sensitive_field_blocked"], matches);
    }
    if (
      matches.some((match) =>
        ["communication_side_effect", "account_settings"].includes(match.category),
      )
    ) {
      if (!request.confirmation?.confirmed) {
        return decision(
          request,
          "confirmation_required",
          "high",
          0.7,
          ["high_risk_requires_confirmation"],
          matches,
        );
      }
    }
    if (request.action_type === "read_current_screen" || request.action_type === "highlight_element") {
      return decision(request, "allowed", "low", 0.05, ["safe_read_action"], matches);
    }
    const score = matches.some((match) => match.category === "medium_form_action") ? 0.45 : 0.1;
    const riskLevel: PolicyRiskLevel = score >= 0.35 ? "medium" : "low";
    return decision(request, "allowed", riskLevel, score, ["safe_action_allowed"], matches);
  }
}

export function normalizePolicyText(value: string): string {
  return value
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function containsPhrase(text: string, phrases: readonly string[]): boolean {
  const normalized = normalizePolicyText(text);
  return phrases.some((phrase) => {
    const normalizedPhrase = normalizePolicyText(phrase);
    return normalized === normalizedPhrase || normalized.includes(` ${normalizedPhrase} `) || normalized.startsWith(`${normalizedPhrase} `) || normalized.endsWith(` ${normalizedPhrase}`);
  });
}

function isSensitiveField(request: ActionPolicyRequest): boolean {
  const text = normalizePolicyText(`${request.element_label ?? ""} ${request.input_type ?? ""}`);
  return request.input_type === "password" || actionSafetyRules.sensitive_field_phrases.some((phrase) => text.includes(normalizePolicyText(phrase)));
}

function domainAllowed(url: string, allowedDomains: string[]): boolean {
  if (allowedDomains.length === 0) return false;
  try {
    const host = new URL(url).hostname.toLowerCase().replace(/\.$/u, "");
    return allowedDomains.some((domain) => {
      const normalized = domain.toLowerCase();
      if (normalized.startsWith("*.")) {
        return host.endsWith(`.${normalized.slice(2)}`);
      }
      return host === normalized;
    });
  } catch {
    return false;
  }
}

function decision(
  request: ActionPolicyRequest,
  decisionValue: PolicyDecisionValue,
  riskLevel: PolicyRiskLevel,
  riskScore: number,
  reasonCodes: string[],
  matches: readonly { category: string; phrases: readonly string[] }[] = [],
): PolicyDecision {
  return {
    decision_id: "deterministic-test-id",
    decision: decisionValue,
    risk_level: riskLevel,
    risk_score: Math.max(0, Math.min(1, riskScore)),
    requires_confirmation: decisionValue === "confirmation_required",
    reason_codes: [...new Set(reasonCodes)],
    matched_rules: matches.map((match) => ({ rule_id: match.category, category: match.category })),
    actor: request.actor,
    organization_id: request.organization_id,
    session_id: request.session_id ?? null,
    trace_id: request.trace_id,
    created_at: new Date(0).toISOString(),
  };
}
