import { percentile } from "./quantiles";
import { RingBuffer } from "./ringBuffer";

export type LatencyMetricName =
  | "event_lag"
  | "first_audio"
  | "turn"
  | "stt"
  | "llm"
  | "tts"
  | "browser_action"
  | "screen_read";

export type LatencySummary = {
  latest: number | null;
  p50: number | null;
  p95: number | null;
};

export class LatencyMetrics {
  private readonly samples = new Map<LatencyMetricName, RingBuffer<number>>();

  constructor(private readonly capacity: number) {}

  append(name: LatencyMetricName, value: number): void {
    if (!Number.isFinite(value)) return;
    const existing = this.samples.get(name) ?? new RingBuffer<number>(this.capacity);
    existing.push(Math.max(0, value));
    this.samples.set(name, existing);
  }

  summary(name: LatencyMetricName): LatencySummary {
    const values = this.samples.get(name)?.toArray() ?? [];
    return {
      latest: values.at(-1) ?? null,
      p50: percentile(values, 50),
      p95: percentile(values, 95),
    };
  }

  length(name: LatencyMetricName): number {
    return this.samples.get(name)?.length ?? 0;
  }
}
