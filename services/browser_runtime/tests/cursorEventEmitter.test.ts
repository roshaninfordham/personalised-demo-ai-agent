import { describe, expect, it } from "vitest";

import { computeCursorPath } from "../src/events/cursorEventEmitter.js";

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
});

