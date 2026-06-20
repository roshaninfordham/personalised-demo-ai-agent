import type { BrowserActionCommand, PolicyDecision, RiskLevel } from "@live-demo-agent/contracts";

import type { BrowserRuntimeConfig } from "../config.js";
import { BrowserRuntimeError } from "../errors.js";
import type { BrowserSessionRecord } from "../browser/browserSession.js";
import { validateNavigationUrl } from "../browser/navigation.js";
import { resolveElement, type ResolvedElement } from "./elementResolver.js";

export type ValidatedAction = {
  command: BrowserActionCommand;
  policyDecision: PolicyDecision;
  riskLevel: RiskLevel;
  resolvedElement?: ResolvedElement;
};

export function validateAction(
  session: BrowserSessionRecord,
  command: BrowserActionCommand,
  config: BrowserRuntimeConfig,
): ValidatedAction {
  if (session.actionInFlight) {
    throw new BrowserRuntimeError("action_in_flight", "Another action is already running.", 409);
  }
  if (command.browser_session_id !== session.browserSessionId) {
    throw new BrowserRuntimeError("browser_session_mismatch", "Browser session mismatch.", 422);
  }
  if (command.action_type === "navigate_to_allowed_url") {
    if (!command.url) {
      throw new BrowserRuntimeError("missing_url", "Navigation action requires a URL.", 422);
    }
    const validation = validateNavigationUrl(command.url, {
      appEnv: config.appEnv,
      allowLocalProductUrls: config.allowLocalProductUrls,
      allowedDomains: session.allowedDomains,
      blockExternalNavigation: config.browserBlockExternalNavigation,
      maxUrlLength: 2048,
    });
    if (!validation.ok) {
      throw new BrowserRuntimeError(validation.errorCode, validation.message, 422);
    }
    return { command, policyDecision: "allowed", riskLevel: "low" };
  }
  if (["click_element", "highlight_element", "type_into_element"].includes(command.action_type)) {
    if (!command.element_id) {
      throw new BrowserRuntimeError("missing_element_id", "Element action requires element_id.", 422);
    }
    const resolvedElement = resolveElement(session, command.element_id);
    const { element } = resolvedElement;
    if (!element.visible) {
      throw new BrowserRuntimeError("element_not_visible", "Element is not visible.", 409);
    }
    if (!element.enabled) {
      throw new BrowserRuntimeError("element_not_enabled", "Element is not enabled.", 409);
    }
    if (element.risk_level === "blocked" && !(config.appEnv === "local" && config.allowDestructiveActions)) {
      throw new BrowserRuntimeError("action_blocked_by_policy", "Action is blocked by policy.", 403);
    }
    const confirmed = command.policy_context?.["user_confirmed"] === true;
    if (element.risk_level === "high" && config.requireConfirmationForHighRisk && !confirmed) {
      return {
        command,
        policyDecision: "confirmation_required",
        riskLevel: element.risk_level,
        resolvedElement,
      };
    }
    if (command.action_type === "type_into_element") {
      if (element.inputType === "password" || /password|secret|token/i.test(element.label)) {
        throw new BrowserRuntimeError("secret_field_blocked", "Secret-like fields cannot be typed into.", 403);
      }
    }
    return {
      command,
      policyDecision: "allowed",
      riskLevel: element.risk_level,
      resolvedElement,
    };
  }
  return { command, policyDecision: "allowed", riskLevel: "low" };
}

