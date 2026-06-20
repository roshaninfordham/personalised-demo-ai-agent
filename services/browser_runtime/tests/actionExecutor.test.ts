import { describe, expect, it } from "vitest";

import type { BrowserActionCommand } from "@live-demo-agent/contracts";
import { ActionExecutor } from "../src/actions/actionExecutor.js";
import { getConfig } from "../src/config.js";
import type { BrowserSessionRecord } from "../src/browser/browserSession.js";
import type { BrowserEventPublisher } from "../src/events/browserEventPublisher.js";
import type { CursorEventEmitter } from "../src/events/cursorEventEmitter.js";
import type { ScreenReader } from "../src/screen/screenReader.js";

const config = getConfig({ APP_ENV: "local", ALLOW_LOCAL_PRODUCT_URLS: "true" });

describe("action executor", () => {
  it("returns confirmation_required for high-risk element actions before Playwright execution", async () => {
    const executor = new ActionExecutor(
      config,
      noopEvents(),
      noopCursor(),
      {} as ScreenReader,
    );

    const result = await executor.execute(sessionWithHighRiskElement(), command());

    expect(result.success).toBe(false);
    expect(result.policy_decision).toBe("confirmation_required");
    expect(result.error_code).toBe("confirmation_required");
  });
});

function sessionWithHighRiskElement(): BrowserSessionRecord {
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
        "el_export",
        {
          element_id: "el_export",
          role: "button",
          label: "Export Data",
          bbox: { x: 0, y: 0, width: 100, height: 40 },
          visible: true,
          enabled: true,
          risk_level: "high",
          confidence: 0.9,
          tagName: "button",
          inputType: undefined,
          href: undefined,
          placeholder: undefined,
          ariaLabel: undefined,
          text: "Export Data",
          surroundingText: "Export Data",
          selectorHint: "[data-test=\"export\"]",
          elementFingerprint: "fp_export",
        },
      ],
    ]),
    currentSafeActions: [],
    actionInFlight: false,
    cursorPosition: { x: 0, y: 0 },
    screenIdsByHash: new Map(),
  };
}

function command(): BrowserActionCommand {
  return {
    command_id: "00000000-0000-0000-0000-000000000030",
    session_id: "00000000-0000-0000-0000-000000000010",
    browser_session_id: "00000000-0000-0000-0000-000000000100",
    action_type: "click_element",
    element_id: "el_export",
    created_at: new Date().toISOString(),
  };
}

function noopEvents(): BrowserEventPublisher {
  return {
    publish: () => Promise.resolve(undefined),
  } as unknown as BrowserEventPublisher;
}

function noopCursor(): CursorEventEmitter {
  return {} as CursorEventEmitter;
}
