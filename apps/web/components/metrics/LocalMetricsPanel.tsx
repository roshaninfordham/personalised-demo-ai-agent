import { Card, CardBody } from "../ui/Card";

const localMetrics = [
  ["Active sessions", "0", "fake/local baseline"],
  ["Browser actions", "event-driven", "from live event stream"],
  ["Policy blocks", "tracked", "blocked unsafe actions"],
  ["First audio", "provider-dependent", "see Grafana when enabled"],
  ["Event lag", "client-measured", "shown in live debug panel"],
  ["Lead summaries", "queued/generated", "post-demo cold path"],
] as const;

export function LocalMetricsPanel({ compact = false }: { compact?: boolean }) {
  return (
    <Card>
      <CardBody className="stack">
        <div className="panel-title">
          <h2>{compact ? "Local metrics" : "Local Metrics Panel"}</h2>
          <span className="badge badge-warning">observability optional</span>
        </div>
        <div className="metric-grid">
          {localMetrics.map(([label, value, detail]) => (
            <div className="metric-card" key={label}>
              <strong>{label}</strong>
              <span className="metric-value">{value}</span>
              <p className="muted">{detail}</p>
            </div>
          ))}
        </div>
        <p className="muted">
          If Grafana is not running, start it with <code>make up-observability</code>.
        </p>
      </CardBody>
    </Card>
  );
}
