"use client";

import type { CursorState, ElementHighlightState, LiveDemoClientState } from "../lib/events/eventTypes";

export function useCursorOverlay(state: LiveDemoClientState): {
  cursor: CursorState;
  highlights: ElementHighlightState[];
} {
  return {
    cursor: state.cursor,
    highlights: Array.from(state.highlights.values()),
  };
}
