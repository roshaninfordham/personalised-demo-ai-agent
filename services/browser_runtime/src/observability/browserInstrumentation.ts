import { browserMetrics } from "./metrics.js";

export function recordBrowserAction(
  actionType: string,
  riskLevel: string,
  result: "success" | "failed" | "blocked",
  latencyMs: number,
): void {
  browserMetrics.increment("live_demo_browser_actions_total", {
    action_type: actionType,
    risk_level: riskLevel,
    result,
  });
  browserMetrics.observe("live_demo_browser_action_latency_seconds", latencyMs / 1000, {
    action_type: actionType,
    risk_level: riskLevel,
    result,
  });
}

export function recordScreenRead(result: "success" | "failed", latencyMs: number): void {
  browserMetrics.observe("live_demo_browser_screen_read_latency_seconds", latencyMs / 1000, {
    result,
  });
}
