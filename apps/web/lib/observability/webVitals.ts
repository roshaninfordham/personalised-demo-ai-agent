import { observeClientMetric } from "./clientMetrics";

export function recordWebVital(name: string, value: number): void {
  observeClientMetric("live_demo_web_vital_seconds", value / 1000, {
    operation: name.toLowerCase(),
  });
}
