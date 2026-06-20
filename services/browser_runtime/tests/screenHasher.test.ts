import { describe, expect, it } from "vitest";

import { elementFingerprint, hashScreen, normalizeUrlPath, screenIdFromHash } from "../src/screen/screenHasher.js";

describe("screen hashing", () => {
  it("is deterministic and removes volatile query params", () => {
    expect(normalizeUrlPath("https://example.com/Dashboard/?utm_source=x&t=1#a")).toBe(
      "example.com/dashboard?",
    );
    const input = {
      url: "https://example.com/dashboard",
      visibleText: "Dashboard Revenue Metrics",
      accessibility: [{ role: "button", name: "Add Metric", depth: 1 }],
      elements: [],
    };
    expect(hashScreen(input)).toBe(hashScreen(input));
  });

  it("generates deterministic screen ids", () => {
    const existing = new Map<string, string>();
    expect(screenIdFromHash("abcdef1234567890zzz", existing)).toBe("screen_abcdef1234567890");
  });

  it("fingerprints meaningful element attributes", () => {
    const first = elementFingerprint({
      role: "button",
      label: "Add",
      tagName: "button",
      bbox: { x: 1, y: 2 },
    });
    const second = elementFingerprint({
      role: "button",
      label: "Delete",
      tagName: "button",
      bbox: { x: 1, y: 2 },
    });
    expect(first).not.toBe(second);
  });
});

