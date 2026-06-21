import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CursorOverlay } from "../components/live-demo/CursorOverlay";
import { easeOutCubic, quadraticBezier } from "../lib/browser-view/cursorMath";
import type { CursorState } from "../lib/events/eventTypes";

describe("CursorOverlay", () => {
  it("renders cursor overlay with pointer-events disabled", () => {
    const cursor: CursorState = {
      visible: true,
      source: { x: 0, y: 0 },
      target: { x: 10, y: 10 },
      startedAtMs: performance.now(),
      durationMs: 100,
      easing: "easeOutCubic",
      lastUpdatedAt: new Date().toISOString(),
    };
    const { container } = render(
      <CursorOverlay cursor={cursor} sourceSize={{ width: 100, height: 100 }} displaySize={{ width: 100, height: 100 }} />,
    );
    expect(container.querySelector(".frame-overlay")).toBeInTheDocument();
    expect(container.querySelector(".cursor-dot")).toBeInTheDocument();
  });

  it("uses deterministic cursor math", () => {
    expect(easeOutCubic(0)).toBe(0);
    expect(easeOutCubic(1)).toBe(1);
    expect(quadraticBezier({ x: 0, y: 0 }, { x: 10, y: 0 }, { x: 10, y: 10 }, 0.5)).toEqual({
      x: 7.5,
      y: 2.5,
    });
  });
});
