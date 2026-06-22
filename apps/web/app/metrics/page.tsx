import Link from "next/link";

import { LocalMetricsPanel } from "../../components/metrics/LocalMetricsPanel";
import { MetricsDashboardLink } from "../../components/metrics/MetricsDashboardLink";
import { Card, CardBody } from "../../components/ui/Card";

export default function MetricsPage() {
  return (
    <main className="page stack">
      <div className="page-heading">
        <div>
          <h1>Metrics & Analytics</h1>
          <p className="muted">
            Local operational metrics, readiness links, and shortcuts to the optional observability
            stack.
          </p>
        </div>
        <div className="row">
          <MetricsDashboardLink />
          <Link className="button button-secondary" href="/observability">
            Observability
          </Link>
        </div>
      </div>

      <LocalMetricsPanel />

      <Card>
        <CardBody className="stack">
          <h2>Expected Golden Signals</h2>
          <div className="metric-grid">
            {[
              "Active sessions",
              "Session count",
              "Browser action count",
              "Policy blocks",
              "First audio latency",
              "LLM/STT/TTS latency",
              "Browser action latency",
              "Event lag",
            ].map((item) => (
              <div className="metric-card" key={item}>
                <strong>{item}</strong>
                <p className="muted">Available in Prometheus/Grafana when observability is running.</p>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </main>
  );
}
