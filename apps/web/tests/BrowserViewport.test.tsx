import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BrowserViewport } from "../components/live-demo/BrowserViewport";
import { mapBoundingBoxContain, mapPointContain } from "../lib/browser-view/viewportMath";
import { createInitialLiveDemoState } from "../lib/events/eventStore";

describe("BrowserViewport", () => {
  it("shows an empty state before frame", () => {
    const state = createInitialLiveDemoState("00000000-0000-0000-0000-000000000010");
    render(
      <BrowserViewport
        frame={null}
        cursor={state.cursor}
        highlights={[]}
        ripples={[]}
        scrollIndicators={[]}
        connectionStatus="idle"
      />,
    );
    expect(screen.getAllByText("Opening the product...")[0]).toBeInTheDocument();
  });

  it("renders screenshot frame and stale overlay", () => {
    const state = createInitialLiveDemoState("00000000-0000-0000-0000-000000000010");
    render(
      <BrowserViewport
        frame={{
          screenId: "screen_1",
          screenHash: "hash",
          imageUrl: "https://example.com/frame.webp",
          width: 1440,
          height: 900,
          updatedAt: "2026-06-20T12:00:00.000Z",
          stale: true,
        }}
        cursor={state.cursor}
        highlights={[]}
        ripples={[]}
        scrollIndicators={[]}
        connectionStatus="connected"
      />,
    );
    expect(screen.getByAltText("Controlled browser screenshot")).toBeInTheDocument();
    expect(screen.getByText("Frame stale")).toBeInTheDocument();
  });

  it("maps contain coordinates", () => {
    expect(mapPointContain({ x: 50, y: 50 }, { width: 100, height: 100 }, { width: 200, height: 100 })).toEqual({
      x: 100,
      y: 50,
    });
    expect(mapBoundingBoxContain({ x: 0, y: 0, width: 50, height: 50 }, { width: 100, height: 100 }, { width: 100, height: 200 })).toEqual({
      left: 0,
      top: 50,
      width: 50,
      height: 50,
    });
  });
});
