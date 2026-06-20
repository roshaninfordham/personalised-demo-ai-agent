import { createHash } from "node:crypto";

import type { InternalElement } from "./elementExtractor.js";
import type { AccessibilityNode } from "./accessibilityExtractor.js";

const volatileQueryParams = [
  /^utm_/i,
  /^fbclid$/i,
  /^gclid$/i,
  /^timestamp$/i,
  /^t$/i,
  /^cache$/i,
  /^session$/i,
  /^token$/i,
];
const stopwords = new Set([
  "the",
  "and",
  "or",
  "a",
  "an",
  "to",
  "of",
  "in",
  "for",
  "on",
  "with",
  "is",
  "are",
]);

export function hashScreen(input: {
  url: string;
  visibleText: string;
  accessibility: AccessibilityNode[];
  elements: InternalElement[];
}): string {
  const parts = [
    normalizeUrlPath(input.url),
    topVisibleTextKeywords(input.visibleText).join(" "),
    input.accessibility
      .slice(0, 100)
      .map((node) => `${node.role}:${normalizeText(node.name)}`)
      .join("|"),
    input.elements
      .slice(0, 100)
      .map(
        (element) =>
          `${element.role}:${shortHash(element.label)}:${String(grid(element.bbox.x))}:${String(
            grid(element.bbox.y),
          )}`,
      )
      .join("|"),
  ];
  return sha256(parts.join("\n"));
}

export function screenIdFromHash(hash: string, existing: Map<string, string>): string {
  const base = `screen_${hash.slice(0, 16)}`;
  const found = existing.get(base);
  if (found === undefined || found === hash) {
    existing.set(base, hash);
    return base;
  }
  let suffix = 2;
  while (existing.has(`${base}_${String(suffix)}`)) {
    suffix += 1;
  }
  const id = `${base}_${String(suffix)}`;
  existing.set(id, hash);
  return id;
}

export function elementFingerprint(element: {
  role: string;
  label: string;
  tagName: string;
  inputType?: string | undefined;
  surroundingText?: string | undefined;
  bbox: { x: number; y: number };
}): string {
  return sha256(
    [
      element.role,
      normalizeText(element.label),
      normalizeText(element.tagName),
      normalizeText(element.inputType ?? ""),
      normalizeText(element.surroundingText ?? "").slice(0, 120),
      `${String(grid(element.bbox.x))}:${String(grid(element.bbox.y))}`,
    ].join("|"),
  );
}

export function elementId(role: string, fingerprint: string, existing: Set<string>): string {
  const base = `el_${slug(role)}_${fingerprint.slice(0, 12)}`;
  if (!existing.has(base)) {
    existing.add(base);
    return base;
  }
  let suffix = 2;
  while (existing.has(`${base}_${String(suffix)}`)) {
    suffix += 1;
  }
  const id = `${base}_${String(suffix)}`;
  existing.add(id);
  return id;
}

export function actionId(actionType: string, elementIdValue: string): string {
  return `act_${slug(actionType)}_${slug(elementIdValue)}`;
}

export function normalizeUrlPath(url: string): string {
  const parsed = new URL(url);
  parsed.hash = "";
  for (const key of [...parsed.searchParams.keys()]) {
    if (volatileQueryParams.some((pattern) => pattern.test(key))) {
      parsed.searchParams.delete(key);
    }
  }
  const path = parsed.pathname === "/" ? "/" : parsed.pathname.replace(/\/+$/, "").toLowerCase();
  return `${parsed.hostname.toLowerCase()}${path}?${parsed.searchParams.toString()}`;
}

function topVisibleTextKeywords(text: string): string[] {
  const seen = new Map<string, number>();
  for (const token of normalizeText(text).split(" ")) {
    if (token.length < 2 || stopwords.has(token)) {
      continue;
    }
    seen.set(token, (seen.get(token) ?? 0) + 1);
  }
  return [...seen.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, 100)
    .map(([token]) => token);
}

function normalizeText(text: string): string {
  return text.toLowerCase().replace(/[^\p{L}\p{N}\s_-]/gu, " ").replace(/\s+/g, " ").trim();
}

function grid(value: number): number {
  return Math.round(value / 80);
}

function sha256(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

function shortHash(value: string): string {
  return sha256(normalizeText(value)).slice(0, 8);
}

function slug(value: string): string {
  return normalizeText(value).replace(/\s+/g, "_").replace(/_+/g, "_") || "unknown";
}
