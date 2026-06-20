export const blockedKeywords = [
  "delete",
  "remove",
  "destroy",
  "drop",
  "wipe",
  "erase",
  "reset account",
  "close account",
  "cancel subscription",
  "payment",
  "billing",
  "purchase",
  "checkout",
  "pay now",
  "send email",
  "send invite",
  "invite user",
  "publish",
  "go live",
  "deploy",
  "upgrade",
  "connect bank",
  "connect integration",
  "revoke",
  "disable account",
];

export const highRiskKeywords = [
  "submit",
  "save changes",
  "export",
  "download",
  "invite",
  "send",
  "connect",
  "sync",
  "authorize",
  "install",
  "change plan",
  "settings",
  "admin",
  "api key",
  "token",
  "webhook",
];

export const mediumRiskKeywords = [
  "create",
  "add",
  "new",
  "edit",
  "update",
  "filter",
  "apply",
  "generate",
  "import",
];

export const lowRiskKeywords = [
  "view",
  "open",
  "show",
  "dashboard",
  "reports",
  "analytics",
  "metrics",
  "back",
  "next",
  "search",
  "scroll",
  "learn more",
];

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

