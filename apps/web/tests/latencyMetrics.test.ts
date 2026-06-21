import { describe, expect, it } from "vitest";

import { LatencyMetrics } from "../lib/metrics/latencyMetrics";
import { percentile } from "../lib/metrics/quantiles";
import { RingBuffer } from "../lib/metrics/ringBuffer";

describe("latency metrics", () => {
  it("computes p50 and p95 deterministically", () => {
    expect(percentile([10, 20, 30, 40, 50], 50)).toBe(30);
    expect(percentile([10, 20, 30, 40, 50], 95)).toBeCloseTo(48);
  });

  it("caps ring buffers", () => {
    const buffer = new RingBuffer<number>(3);
    buffer.push(1);
    buffer.push(2);
    buffer.push(3);
    buffer.push(4);
    expect(buffer.toArray()).toEqual([2, 3, 4]);
  });

  it("tracks latest and quantiles", () => {
    const metrics = new LatencyMetrics(5);
    metrics.append("event_lag", -1);
    metrics.append("event_lag", 20);
    metrics.append("event_lag", 40);
    expect(metrics.summary("event_lag").latest).toBe(40);
    expect(metrics.summary("event_lag").p50).toBe(20);
  });
});
