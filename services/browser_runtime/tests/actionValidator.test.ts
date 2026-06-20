import { describe, expect, it } from "vitest";

import { validateAction } from "../src/actions/actionValidator.js";
import { getConfig } from "../src/config.js";
import type { BrowserSessionRecord } from "../src/browser/browserSession.js";

const config = getConfig({ APP_ENV: "local", ALLOW_LOCAL_PRODUCT_URLS: "true" });

function sessionWithElement(riskLevel: "low" | "high" | "blocked", visible = true): BrowserSessionRecord {
  return {
    browserSessionId: "00000000-0000-0000-0000-000000000100",
    organizationId: "00000000-0000-0000-0000-000000000001",
    demoSessionId: "00000000-0000-0000-0000-000000000010",
    productId: "00000000-0000-0000-0000-000000000020",
    allowedDomains: ["example.com"],
    status: "active",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + 1000).toISOString(),
    context: {} as BrowserSessionRecord["context"],
    page: { locator: () => ({ first: () => ({}) }) } as unknown as BrowserSessionRecord["page"],
    currentElements: new Map([
      [
        "el_button",
        {
          element_id: "el_button",
          role: "button",
          label: "Test",
          bbox: { x: 0, y: 0, width: 10, height: 10 },
          visible,
          enabled: true,
          risk_level: riskLevel,
          confidence: 1,
          tagName: "button",
          inputType: undefined,
          href: undefined,
          placeholder: undefined,
          ariaLabel: undefined,
          text: "Test",
          selectorHint: "[data-test]",
          elementFingerprint: "fp",
          surroundingText: "Test",
        },
      ],
    ]),
    currentSafeActions: [],
    actionInFlight: false,
    cursorPosition: { x: 0, y: 0 },
    screenIdsByHash: new Map(),
  };
}

describe("action validator", () => {
  it("rejects blocked and invisible actions", () => {
    expect(() =>
      validateAction(sessionWithElement("blocked"), command("click_element"), config),
    ).toThrow();
    expect(() => validateAction(sessionWithElement("low", false), command("click_element"), config)).toThrow();
  });

  it("requires confirmation for high-risk actions", () => {
    const result = validateAction(sessionWithElement("high"), command("click_element"), config);
    expect(result.policyDecision).toBe("confirmation_required");
  });

  it("allows low-risk actions", () => {
    const result = validateAction(sessionWithElement("low"), command("click_element"), config);
    expect(result.policyDecision).toBe("allowed");
  });
});

function command(actionType: "click_element") {
  return {
    command_id: "00000000-0000-0000-0000-000000000030",
    session_id: "00000000-0000-0000-0000-000000000010",
    browser_session_id: "00000000-0000-0000-0000-000000000100",
    action_type: actionType,
    created_at: new Date().toISOString(),
    element_id: "el_button",
  };
}
