export type MetricLabels = Record<string, string | number | boolean>;

const allowedLabels = new Set([
  "service",
  "environment",
  "operation",
  "status",
  "provider",
  "purpose",
  "transport_provider",
  "action_type",
  "risk_level",
  "policy_decision",
  "policy_type",
  "decision",
  "reason_code",
  "phase",
  "error_code",
  "route",
  "method",
  "trigger",
  "result",
  "job_type",
  "source_type",
  "retrieval_type",
  "event_type_group",
  "component",
  "severity",
  "dry_run",
  "mode",
  "token_type",
  "format",
]);

const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/iu;
const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/u;
const urlPattern = /^[a-z][a-z0-9+.-]*:\/\//iu;
const idPattern = /^[0-9a-f]{16,64}$/iu;

export class BrowserMetricRegistry {
  private readonly counters = new Map<string, number>();
  private readonly gauges = new Map<string, number>();
  private readonly histograms = new Map<string, number[]>();

  constructor(
    private readonly service = "browser-runtime",
    private readonly environment = process.env.DEPLOYMENT_ENVIRONMENT ?? process.env.APP_ENV ?? "local",
  ) {}

  increment(name: string, labels: MetricLabels = {}, value = 1): void {
    const key = this.key(name, labels);
    this.counters.set(key, (this.counters.get(key) ?? 0) + value);
  }

  setGauge(name: string, value: number, labels: MetricLabels = {}): void {
    this.gauges.set(this.key(name, labels), value);
  }

  observe(name: string, value: number, labels: MetricLabels = {}): void {
    const key = this.key(name, labels);
    const current = this.histograms.get(key) ?? [];
    current.push(value);
    this.histograms.set(key, current);
  }

  renderPrometheus(): string {
    const lines: string[] = [];
    for (const [key, value] of [...this.counters.entries()].sort()) {
      lines.push(`${key} ${String(value)}`);
    }
    for (const [key, value] of [...this.gauges.entries()].sort()) {
      lines.push(`${key} ${String(value)}`);
    }
    for (const [key, values] of [...this.histograms.entries()].sort()) {
      const total = values.reduce((sum, item) => sum + item, 0);
      lines.push(`${key}_count ${String(values.length)}`);
      lines.push(`${key}_sum ${String(total)}`);
    }
    return `${lines.join("\n")}\n`;
  }

  private key(name: string, labels: MetricLabels): string {
    const merged = { service: this.service, environment: this.environment, ...labels };
    validateLabels(merged);
    const rendered = Object.entries(merged)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([label, value]) => `${label}="${labelValue(value)}"`)
      .join(",");
    return rendered.length === 0 ? name : `${name}{${rendered}}`;
  }
}

function labelValue(value: string | number | boolean): string {
  return typeof value === "string" ? value.toLowerCase() : String(value).toLowerCase();
}

export const browserMetrics = new BrowserMetricRegistry();

export function validateLabels(labels: MetricLabels): void {
  for (const [label, raw] of Object.entries(labels)) {
    if (!allowedLabels.has(label)) {
      throw new Error(`Metric label is not allowed: ${label}`);
    }
    const value = String(raw).trim();
    if (
      value.length > 100 ||
      uuidPattern.test(value) ||
      emailPattern.test(value) ||
      urlPattern.test(value) ||
      (idPattern.test(value) && label !== "error_code")
    ) {
      throw new Error(`Metric label value is high-cardinality: ${label}`);
    }
  }
}
