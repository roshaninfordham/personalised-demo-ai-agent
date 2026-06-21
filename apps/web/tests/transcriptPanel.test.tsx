import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TranscriptPanel } from "../components/live-demo/TranscriptPanel";
import type { TranscriptItem } from "../lib/events/eventTypes";

describe("TranscriptPanel", () => {
  it("renders empty state", () => {
    render(<TranscriptPanel items={[]} />);
    expect(screen.getByText("No transcript yet")).toBeInTheDocument();
  });

  it("renders partial, final, and interrupted states", () => {
    const items: TranscriptItem[] = [
      {
        transcriptEventId: "t1",
        speaker: "assistant",
        chunkType: "partial",
        text: "Working",
        createdAt: "2026-06-20T12:00:00.000Z",
      },
      {
        transcriptEventId: "t2",
        speaker: "assistant",
        chunkType: "interrupted",
        text: "Actually",
        createdAt: "2026-06-20T12:00:01.000Z",
      },
    ];
    render(<TranscriptPanel items={items} />);
    expect(screen.getByText("Working")).toBeInTheDocument();
    expect(screen.getByText("interrupted")).toBeInTheDocument();
  });
});
