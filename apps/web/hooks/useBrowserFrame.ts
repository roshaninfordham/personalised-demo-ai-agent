"use client";

import type { BrowserFrameState } from "../lib/browser-view/frameStore";
import type { LiveDemoClientState } from "../lib/events/eventTypes";

export function useBrowserFrame(state: LiveDemoClientState): BrowserFrameState | null {
  return state.currentFrame;
}
