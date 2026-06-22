import { actionSafetyRules } from "@live-demo-agent/policies";

const categories = actionSafetyRules.categories;

export const blockedKeywords = categories
  .filter((category) => category.risk_level === "blocked")
  .flatMap((category) => [...category.phrases]);

export const highRiskKeywords = categories
  .filter((category) => category.risk_level === "high")
  .flatMap((category) => [...category.phrases]);

export const mediumRiskKeywords = categories
  .filter((category) => category.risk_level === "medium")
  .flatMap((category) => [...category.phrases]);

export const lowRiskKeywords = categories
  .filter((category) => category.risk_level === "low")
  .flatMap((category) => [...category.phrases]);

export const sensitiveFieldPhrases = [...actionSafetyRules.sensitive_field_phrases];

export function containsPhrase(text: string, phrases: string[]): boolean {
  const normalized = normalizeRiskText(text);
  return phrases.some((phrase) => {
    const normalizedPhrase = normalizeRiskText(phrase);
    return new RegExp(`(^|\\s)${escapeRegex(normalizedPhrase)}($|\\s)`, "u").test(normalized);
  });
}

export function normalizeRiskText(text: string): string {
  return text.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ").replace(/\s+/g, " ").trim();
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
