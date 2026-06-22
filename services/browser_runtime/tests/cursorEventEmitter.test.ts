import { describe, expect, it } from "vitest";

import type { BrowserSessionRecord } from "../src/browser/browserSession.js";
import { getConfig } from "../src/config.js";
import { BrowserEventPublisher } from "../src/events/browserEventPublisher.js";
import { computeCursorPath, CursorEventEmitter } from "../src/events/cursorEventEmitter.js";
import type { BrowserEventType } from "../src/events/eventTypes.js";
import type { RedisClientLike } from "../src/redis/redisClient.js";
import type { InternalElement } from "../src/screen/elementExtractor.js";

describe("cursor event emitter", () => {
  it("bounds duration and is deterministic", () => {
    const first = computeCursorPath(
      { x: 0, y: 0 },
      { x: 500, y: 200 },
      { width: 1000, height: 800 },
      250,
      700,
      "action_1",
    );
    const second = computeCursorPath(
      { x: 0, y: 0 },
      { x: 500, y: 200 },
      { width: 1000, height: 800 },
      250,
      700,
      "action_1",
    );
    expect(first).toEqual(second);
    expect(first.duration_ms).toBeGreaterThanOrEqual(250);
    expect(first.duration_ms).toBeLessThanOrEqual(700);
  });

  it("publishes highlight metadata needed to align the frontend overlay", async () => {
    const config = getConfig({ ELEMENT_HIGHLIGHT_DURATION_MS: "900" });
    const publisher = new CapturingPublisher(config);
    const emitter = new CursorEventEmitter(config, publisher);
    await emitter.emitHighlight(fakeSession(), {
      element_id: "el_sign_up",
      role: "link",
      label: "Sign up",
      bbox: { x: 512, y: 640, width: 92, height: 28 },
      visible: true,
      enabled: true,
      risk_level: "medium",
      confidence: 0.94,
      tagName: "a",
      inputType: undefined,
      href: "/fixtures/login-product/signup",
      placeholder: undefined,
      ariaLabel: undefined,
      text: "Sign up",
      surroundingText: "Don't have an account? Sign up",
      selectorHint: "[data-live-demo-agent-el-index=\"4\"]",
      elementFingerprint: "fingerprint",
    });
    expect(publisher.events).toEqual([
      {
        eventType: "browser.element.highlight",
        payload: {
          element_id: "el_sign_up",
          bbox: { x: 512, y: 640, width: 92, height: 28 },
          label: "Sign up",
          risk_level: "medium",
          duration_ms: 900,
        },
      },
    ]);
  });
});

class CapturingPublisher extends BrowserEventPublisher {
  readonly events: Array<{ eventType: BrowserEventType; payload: Record<string, unknown> }> = [];

  constructor(config: ReturnType<typeof getConfig>) {
    super(config, redisStub);
  }

  override publish(
    _session: BrowserSessionRecord,
    eventType: BrowserEventType,
    payload: Record<string, unknown>,
  ): Promise<void> {
    this.events.push({ eventType, payload });
    return Promise.resolve();
  }
}

function fakeSession(): BrowserSessionRecord {
  return {
    browserSessionId: "browser_session_1",
    organizationId: "org_1",
    demoSessionId: "session_1",
    productId: "product_1",
    allowedDomains: ["localhost"],
    status: "active",
    createdAt: "2026-06-22T00:00:00.000Z",
    updatedAt: "2026-06-22T00:00:00.000Z",
    expiresAt: "2026-06-22T01:00:00.000Z",
    context: {} as BrowserSessionRecord["context"],
    page: {} as BrowserSessionRecord["page"],
    currentElements: new Map<string, InternalElement>(),
    currentSafeActions: [],
    actionInFlight: false,
    cursorPosition: { x: 0, y: 0 },
    screenIdsByHash: new Map<string, string>(),
  };
}

const redisStub: RedisClientLike = {
  ping: () => Promise.resolve("PONG"),
  get: () => Promise.resolve(null),
  set: () => Promise.resolve("OK"),
  del: () => Promise.resolve(0),
  xadd: () => Promise.resolve("0-0"),
  quit: () => Promise.resolve(undefined),
};
