import type { RiskLevel } from "@live-demo-agent/contracts";

import {
  blockedKeywords,
  containsPhrase,
  highRiskKeywords,
  lowRiskKeywords,
  mediumRiskKeywords,
  sensitiveFieldPhrases,
} from "./safetyPolicy.js";

export type RiskClassificationInput = {
  role: string;
  label: string;
  tagName: string;
  inputType?: string | undefined;
  href?: string | undefined;
  currentUrl: string;
  surroundingText: string;
  formContext?: string | undefined;
  recipeNeverClick: string[];
  globalNeverClick: string[];
  allowedDomains: string[];
};

export type RiskClassification = {
  riskLevel: RiskLevel;
  riskScore: number;
  reason: string;
};

export function classifyElementRisk(input: RiskClassificationInput): RiskClassification {
  const combined = [input.label, input.surroundingText, input.formContext ?? ""].join(" ");
  if (isSensitiveField(input, combined)) {
    return {
      riskLevel: "blocked",
      riskScore: 1,
      reason: "Sensitive credential or payment field blocked.",
    };
  }
  if (
    containsPhrase(input.label, input.globalNeverClick) ||
    containsPhrase(input.label, input.recipeNeverClick) ||
    containsPhrase(combined, blockedKeywords) ||
    domainRisk(input.href, input.allowedDomains) >= 1
  ) {
    return { riskLevel: "blocked", riskScore: 1, reason: "Blocked by safety policy." };
  }
  if (containsPhrase(input.label, highRiskKeywords)) {
    return { riskLevel: "high", riskScore: 0.7, reason: "High-risk UI label." };
  }
  if (containsPhrase(input.label, mediumRiskKeywords)) {
    return { riskLevel: "medium", riskScore: 0.45, reason: "Medium-risk UI label." };
  }
  const labelRisk = scoreText(input.label);
  const roleRisk = roleScore(input.role, input.inputType);
  const contextRisk = scoreText(input.surroundingText);
  const recipeRisk = containsPhrase(combined, input.recipeNeverClick) ? 1 : 0;
  const hrefRisk = domainRisk(input.href, input.allowedDomains);
  const score = clamp(
    0.35 * labelRisk + 0.15 * roleRisk + 0.25 * contextRisk + 0.2 * recipeRisk + 0.05 * hrefRisk,
  );
  if (score >= 0.85) {
    return { riskLevel: "blocked", riskScore: score, reason: "Risk score blocked action." };
  }
  if (score >= 0.65) {
    return { riskLevel: "high", riskScore: score, reason: "High-risk UI action." };
  }
  if (score >= 0.35) {
    return { riskLevel: "medium", riskScore: score, reason: "Medium-risk UI action." };
  }
  return { riskLevel: "low", riskScore: score, reason: "Low-risk UI action." };
}

function isSensitiveField(input: RiskClassificationInput, combined: string): boolean {
  if (input.inputType?.toLowerCase() === "password") return true;
  if (containsPhrase(input.label, sensitiveFieldPhrases)) return true;
  const fieldLike = input.tagName === "input" || input.role === "input" || input.role === "textarea";
  return fieldLike && containsPhrase(combined, sensitiveFieldPhrases);
}

function scoreText(text: string): number {
  if (containsPhrase(text, highRiskKeywords)) return 0.75;
  if (containsPhrase(text, mediumRiskKeywords)) return 0.45;
  if (containsPhrase(text, lowRiskKeywords)) return 0.05;
  return 0.2;
}

function roleScore(role: string, inputType: string | undefined): number {
  if (inputType === "password") return 1;
  if (["input", "textarea", "select"].includes(role)) return 0.35;
  if (role === "button") return 0.25;
  if (role === "link") return 0.15;
  return 0.1;
}

function domainRisk(href: string | undefined, allowedDomains: string[]): number {
  if (!href || allowedDomains.length === 0) return 0;
  try {
    const host = new URL(href).hostname.toLowerCase();
    return allowedDomains.some((domain) => host === domain || host.endsWith(`.${domain}`)) ? 0 : 1;
  } catch {
    return 0;
  }
}

function clamp(value: number): number {
  return Math.max(0, Math.min(1, value));
}
