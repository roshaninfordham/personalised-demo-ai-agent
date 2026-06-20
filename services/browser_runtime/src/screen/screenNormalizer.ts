import type { ScreenState } from "@live-demo-agent/contracts";

import type { BrowserSessionRecord } from "../browser/browserSession.js";
import { classifyElementRisk } from "../actions/riskClassifier.js";
import { generateSafeActions } from "../actions/actionRanker.js";
import { buildCompactSummary } from "./compactSummary.js";
import type { AccessibilityNode } from "./accessibilityExtractor.js";
import type { DomSummary } from "./domExtractor.js";
import type { InternalElement } from "./elementExtractor.js";
import { elementFingerprint, elementId, hashScreen, screenIdFromHash } from "./screenHasher.js";
import { toPublicElement } from "./elementExtractor.js";

export function normalizeScreen(input: {
  session: BrowserSessionRecord;
  url: string;
  title: string;
  visibleText: string;
  domSummary: DomSummary;
  accessibility: AccessibilityNode[];
  rawElements: Omit<InternalElement, "element_id" | "risk_level" | "confidence" | "elementFingerprint">[];
  screenshotUri: string;
  screenshotArtifactId?: string;
  globalNeverClick: string[];
  actionScoreThreshold: number;
}): { screenState: ScreenState; elements: InternalElement[] } {
  const idSet = new Set<string>();
  const elements = input.rawElements.map((raw) => {
    const fingerprint = elementFingerprint(raw);
    const risk = classifyElementRisk({
      role: raw.role,
      label: raw.label,
      tagName: raw.tagName,
      inputType: raw.inputType,
      href: raw.href,
      currentUrl: input.url,
      surroundingText: raw.surroundingText,
      recipeNeverClick: [],
      globalNeverClick: input.globalNeverClick,
      allowedDomains: input.session.allowedDomains,
    });
    return {
      ...raw,
      element_id: elementId(raw.role, fingerprint, idSet),
      elementFingerprint: fingerprint,
      risk_level: risk.riskLevel,
      confidence: 0.86,
    };
  });
  const screenHash = hashScreen({
    url: input.url,
    visibleText: input.visibleText,
    accessibility: input.accessibility,
    elements,
  });
  const screenId = screenIdFromHash(screenHash, input.session.screenIdsByHash);
  const summaryText = buildCompactSummary({
    title: input.title,
    domSummary: input.domSummary,
    elements,
  });
  const createdAt = new Date().toISOString();
  const screenState: ScreenState = {
    screen_id: screenId,
    session_id: input.session.demoSessionId,
    browser_session_id: input.session.browserSessionId,
    url: input.url,
    title: input.title,
    screen_hash: screenHash,
    visible_text: input.visibleText ? [input.visibleText] : [],
    summary: {
      screen_id: screenId,
      summary: summaryText,
      confidence: 0.86,
      created_at: createdAt,
    },
    elements: elements.map(toPublicElement),
    screenshot_uri: input.screenshotUri,
    confidence: 0.86,
    created_at: createdAt,
  };
  input.session.currentSafeActions = generateSafeActions(
    elements,
    screenHash,
    input.actionScoreThreshold,
  );
  return { screenState, elements };
}

