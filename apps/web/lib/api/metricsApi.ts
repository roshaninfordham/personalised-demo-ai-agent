import { apiRequest } from "./apiClient";
import { metricsSummaryEndpoint } from "./endpoints";

export type MetricsSummary = {
  active_sessions: number;
  sessions_today: number;
  browser_actions_today: number;
  policy_blocks_today: number;
  average_prewarm_ms: number | null;
  average_browser_action_ms: number | null;
  event_lag_ms: number | null;
  observability_enabled: boolean;
  grafana_url: string;
  prometheus_url: string;
};

export function getMetricsSummary(): Promise<MetricsSummary> {
  return apiRequest<MetricsSummary>(metricsSummaryEndpoint(), { timeoutMs: 5000 });
}
