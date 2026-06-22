type Labels = Record<string, string | number | boolean>;

const counters = new Map<string, number>();
const histograms = new Map<string, number[]>();

export function incrementClientMetric(name: string, labels: Labels = {}, value = 1): void {
  const key = metricKey(name, labels);
  counters.set(key, (counters.get(key) ?? 0) + value);
}

export function observeClientMetric(name: string, value: number, labels: Labels = {}): void {
  const key = metricKey(name, labels);
  const current = histograms.get(key) ?? [];
  current.push(value);
  histograms.set(key, current);
}

export function snapshotClientMetrics(): {
  counters: Record<string, number>;
  histograms: Record<string, number[]>;
} {
  return {
    counters: Object.fromEntries([...counters.entries()].sort()),
    histograms: Object.fromEntries([...histograms.entries()].sort()),
  };
}

function metricKey(name: string, labels: Labels): string {
  const rendered = Object.entries(labels)
    .filter(([key]) => !/session_id|trace_id|turn_id|user_id|email/i.test(key))
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}=${String(value).toLowerCase()}`)
    .join(",");
  return rendered.length === 0 ? name : `${name}{${rendered}}`;
}
