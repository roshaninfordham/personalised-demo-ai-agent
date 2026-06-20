import type { BrowserActionType, RiskLevel } from "@live-demo-agent/contracts";

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
};

export function generateSafeActions(
  elements: InternalElement[],
  screenHash: string,
  threshold: number,
): SafeActionInternal[] {
  const expiresAt = new Date(Date.now() + 5 * 60 * 1000).toISOString();
  return elements
    .filter((element) => element.visible && element.enabled && element.risk_level !== "blocked")
    .map((element) => {
      const actionType: BrowserActionType =
        ["input", "textarea", "select"].includes(element.role) ? "type_into_element" : "click_element";
      const riskPenalty = element.risk_level === "high" ? 0.4 : element.risk_level === "medium" ? 0.2 : 0;
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
      };
    })
    .filter((action) => action.score >= threshold || action.risk_level === "low")
    .slice(0, 20);
}

