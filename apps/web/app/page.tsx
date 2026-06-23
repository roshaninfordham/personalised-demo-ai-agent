import Link from "next/link";

import { DemoStartForm } from "../components/demo-start/DemoStartForm";
import { Card, CardBody } from "../components/ui/Card";
import { getPublicConfig } from "../lib/config/publicConfig";

export default function HomePage() {
  const config = getPublicConfig();
  const localEndpoints = [
    ["API", `${config.apiBaseUrl}/healthz`, "session orchestration"],
    ["Browser runtime", `${config.browserRuntimeUrl}/healthz`, "Playwright control"],
    ["Agent runtime", `${config.agentRuntimeUrl}/healthz`, "voice and agent loop"],
    ["Storage", `${config.minioUrl}/minio/health/live`, "artifact storage health"],
    ["LLM provider", config.providerModeLabel, "selected by environment"],
    ["STT/TTS", "voice mode dependent", "text fallback is always available"],
  ] as const;
  return (
    <main className="page landing landing-demo">
      <section className="home-hero">
        <div className="hero-copy">
          <span className="badge badge-success">Local mode: {config.providerModeLabel}</span>
          <h1>Live AI Product Demo Agent</h1>
          <p>
            Enter a product URL. The agent opens it, learns the screen, and gives a live
            interactive demo.
          </p>
          <div className="home-hero-meta" aria-label="Demo capabilities">
            <span>Browser-first live room</span>
            <span>Grounded text fallback</span>
            <span>Safe actions only</span>
          </div>
        </div>
        <Card className="home-start-card">
          <CardBody>
            <DemoStartForm />
          </CardBody>
        </Card>
      </section>

      <section className="home-secondary">
        <Link className="linked-card" href="/metrics">
          Metrics
        </Link>
        <Link className="linked-card" href="/observability">
          Observability
        </Link>
        <Link className="linked-card" href="/docs">
          Docs
        </Link>
      </section>

      <details className="system-status-compact">
        <summary>
          <span>Local endpoints</span>
          <strong>Run make health for real service status</strong>
        </summary>
        <div className="system-status-list">
          {localEndpoints.map(([title, endpoint, detail]) => (
            <div key={title}>
              <span className="badge">local</span>
              <strong>{title}</strong>
              <p className="muted">{detail}</p>
              <code>{endpoint}</code>
            </div>
          ))}
        </div>
      </details>
    </main>
  );
}
