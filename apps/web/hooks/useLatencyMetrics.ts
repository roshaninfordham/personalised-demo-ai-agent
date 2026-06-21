"use client";

import type { LatencyMetricName, LatencySummary } from "../lib/metrics/latencyMetrics";
import type { LiveDemoClientState } from "../lib/events/eventTypes";

export function useLatencyMetrics(state: LiveDemoClientState): Record<LatencyMetricName, LatencySummary> {
  const names: LatencyMetricName[] = [
    "event_lag",
    "first_audio",
    "turn",
    "stt",
    "llm",
    "tts",
    "browser_action",
    "screen_read",
  ];
  return Object.fromEntries(names.map((name) => [name, state.latency.metrics.summary(name)])) as Record<
    LatencyMetricName,
    LatencySummary
  >;
}
