import { observeClientMetric } from "./clientMetrics";

export function recordEventLag(eventType: string, eventCreatedAt: string, now = Date.now()): number {
  const created = Date.parse(eventCreatedAt);
  if (!Number.isFinite(created)) {
    return 0;
  }
  const lagSeconds = Math.max(0, (now - created) / 1000);
  observeClientMetric("live_demo_event_lag_seconds", lagSeconds, {
    event_type_group: eventType.split(".")[0] ?? "unknown",
  });
  return lagSeconds;
}
