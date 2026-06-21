"use client";

import type { LiveDemoClientState, TranscriptItem } from "../lib/events/eventTypes";

export function useTranscript(state: LiveDemoClientState): TranscriptItem[] {
  return state.transcript.items.toArray();
}
