import { browserMetrics } from "./metrics.js";

export type LatencyBudget = {
  operation: string;
  targetMs: number;
  warningMs: number;
  criticalMs: number;
  hotPath: boolean;
};

export const defaultLatencyBudgets: Record<string, LatencyBudget> = {
  browser_action_total: {
    operation: "browser_action_total",
    targetMs: 1000,
    warningMs: 3000,
    criticalMs: 5000,
    hotPath: true,
  },
  screen_read: {
    operation: "screen_read",
    targetMs: 800,
    warningMs: 2000,
    criticalMs: 5000,
    hotPath: true,
  },
  event_publish: {
    operation: "event_publish",
    targetMs: 20,
    warningMs: 100,
    criticalMs: 250,
    hotPath: true,
  },
};

export function checkLatencyBudget(operation: string, durationMs: number): string {
  const budget = defaultLatencyBudgets[operation];
  if (budget === undefined) {
    return "disabled";
  }
  const status =
    durationMs <= budget.targetMs
      ? "ok"
      : durationMs <= budget.warningMs
        ? "warning"
        : durationMs <= budget.criticalMs
          ? "violated"
          : "critical";
  browserMetrics.increment("live_demo_latency_budget_checks_total", { operation, status });
  if (status === "warning" || status === "violated" || status === "critical") {
    browserMetrics.increment("live_demo_latency_budget_violations_total", {
      operation,
      severity: status,
    });
    browserMetrics.observe("live_demo_latency_budget_excess_seconds", durationMs / 1000, {
      operation,
      severity: status,
    });
  }
  return status;
}

export async function observeLatency<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  const started = performance.now();
  try {
    return await fn();
  } finally {
    checkLatencyBudget(operation, performance.now() - started);
  }
}
