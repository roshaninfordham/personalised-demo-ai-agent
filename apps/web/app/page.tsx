import Link from "next/link";

import { DemoStartForm } from "../components/demo-start/DemoStartForm";
import { LocalMetricsPanel } from "../components/metrics/LocalMetricsPanel";
import { MetricsDashboardLink } from "../components/metrics/MetricsDashboardLink";
import { Card, CardBody } from "../components/ui/Card";
import { getPublicConfig } from "../lib/config/publicConfig";

export default function HomePage() {
  const config = getPublicConfig();
  const statusCards = [
    ["API", `${config.apiBaseUrl}/healthz`, "session orchestration"],
    ["Browser runtime", `${config.browserRuntimeUrl}/healthz`, "Playwright control"],
    ["Agent runtime", `${config.agentRuntimeUrl}/healthz`, "voice and agent loop"],
    ["Storage", `${config.minioUrl}/minio/health/live`, "Redis/Postgres/MinIO state"],
    ["LLM provider", "env-configured", "fake/NIM/Ollama/custom"],
    ["STT/TTS", "env-configured", "fake/local/cloud"],
  ] as const;
  return (
    <main className="page landing landing-demo">
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="badge badge-success">Demo readiness: Ready in fake-provider mode</span>
          <h1>Live AI Product Demo Agent</h1>
          <p>
            Enter a product URL, optionally add guidance or a recipe, and start a safe interactive
            demo with browser control, grounded answers, transcript, learning, and post-demo summary.
          </p>
          <div className="hero-actions">
            <Link className="button" href="/demo">
              Open full demo form
            </Link>
            <Link className="button button-secondary" href="/metrics">
              Metrics & Analytics
            </Link>
          </div>
        </div>
        <Card>
          <CardBody>
            <DemoStartForm />
          </CardBody>
        </Card>
      </section>

      <section className="quick-link-grid" aria-label="Quick links">
        <Link href="/demo">Live Demo</Link>
        <Link href="/metrics">Metrics & Analytics</Link>
        <Link href="/observability">Observability</Link>
        <a href="/api/v1/docs">API Docs</a>
        <a href="https://github.com/roshaninfordham/personalised-demo-ai-agent">Repo</a>
        <Link href="/demo">Settings</Link>
      </section>

      <section className="status-grid" aria-label="Provider and service status">
        {statusCards.map(([title, endpoint, detail]) => (
          <Card key={title}>
            <CardBody className="status-card">
              <div className="panel-title">
                <h2>{title}</h2>
                <span className="badge badge-success">configured</span>
              </div>
              <p className="muted">{detail}</p>
              <code>{endpoint}</code>
            </CardBody>
          </Card>
        ))}
      </section>

      <section className="dashboard-strip">
        <div>
          <span className="badge">{config.providerModeLabel}</span>
          <h2>Operator links</h2>
          <p className="muted">
            Grafana and Prometheus are optional. Start them with <code>make up-observability</code>.
          </p>
        </div>
        <div className="row">
          <MetricsDashboardLink />
          <Link className="button button-secondary" href="/observability">
            Observability
          </Link>
        </div>
      </section>

      <LocalMetricsPanel compact />
    </main>
  );
}
