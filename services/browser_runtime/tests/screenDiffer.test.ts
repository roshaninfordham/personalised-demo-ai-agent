import { describe, expect, it } from "vitest";

import { diffScreens, jaccardDistance } from "../src/screen/screenDiffer.js";

describe("screen differ", () => {
  it("computes Jaccard distance", () => {
    expect(jaccardDistance(new Set(["a"]), new Set(["a", "b"]))).toBe(0.5);
  });

  it("detects url and hash change", () => {
    const before = screen("https://example.com/a", "hash_a", ["a"]);
    const after = screen("https://example.com/b", "hash_b", ["b"]);
    const diff = diffScreens(before, after);
    expect(diff.urlChanged).toBe(true);
    expect(diff.hashChanged).toBe(true);
    expect(diff.elementJaccardDistance).toBe(1);
  });
});

function screen(url: string, hash: string, elements: string[]) {
  return {
    screen_id: "screen_a",
    session_id: "00000000-0000-0000-0000-000000000010",
    browser_session_id: "browser",
    url,
    title: "Title",
    screen_hash: hash,
    visible_text: [],
    summary: {
      screen_id: "screen_a",
      summary: "",
      confidence: 1,
      created_at: new Date().toISOString(),
    },
    elements: elements.map((id) => ({
      element_id: id,
      role: "button" as const,
      label: id,
      bbox: { x: 0, y: 0, width: 1, height: 1 },
      visible: true,
      enabled: true,
      risk_level: "low" as const,
      confidence: 1,
    })),
    screenshot_uri: "",
    confidence: 1,
    created_at: new Date().toISOString(),
  };
}

