import { describe, expect, it } from "vitest";

import { checkLatencyBudget } from "../src/observability/latencyBudget.js";
import { BrowserMetricRegistry, validateLabels } from "../src/observability/metrics.js";
import { createTraceContext } from "../src/observability/tracing.js";

describe("browser observability", () => {
  it("creates trace context when traceparent is absent", () => {
    const context = createTraceContext();

    expect(context.traceId).toHaveLength(32);
    expect(context.spanId).toHaveLength(16);
    expect(context.traceparent).toContain(context.traceId);
  });

  it("continues trace context from traceparent", () => {
    const context = createTraceContext("00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01");

    expect(context.traceId).toBe("4bf92f3577b34da6a3ce929d0e0e4736");
  });

  it("rejects high-cardinality labels", () => {
    expect(() => {
      validateLabels({
        service: "browser-runtime",
        environment: "local",
        session_id: "00000000-0000-0000-0000-000000000001",
      });
    },
    ).toThrow(/not allowed/);
    expect(() => {
      validateLabels({ service: "browser-runtime", environment: "local", provider: "a@b.com" });
    },
    ).toThrow(/high-cardinality/);
  });

  it("renders prometheus metrics", () => {
    const registry = new BrowserMetricRegistry("browser-runtime", "local");
    registry.increment("live_demo_browser_actions_total", {
      action_type: "click_element",
      risk_level: "low",
      result: "success",
    });

    expect(registry.renderPrometheus()).toContain("live_demo_browser_actions_total");
  });

  it("checks latency budgets", () => {
    expect(checkLatencyBudget("browser_action_total", 6000)).toBe("critical");
  });
});
