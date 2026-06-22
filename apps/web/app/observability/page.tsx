import { getPublicConfig } from "../../lib/config/publicConfig";

export default function ObservabilityPage() {
  const config = getPublicConfig();
  const links = [
    ["Grafana", config.grafanaUrl, "Dashboards: realtime UX, browser reliability, agent quality, cost/usage"],
    ["Prometheus", config.prometheusUrl, "Prometheus metrics and target health"],
    ["Jaeger/Tempo", config.jaegerUrl, "Distributed traces"],
    ["Loki", config.lokiUrl, "Structured JSON logs"],
  ] as const;

  return (
    <main className="page stack">
      <div className="page-heading">
        <div>
          <h1>Observability</h1>
          <p className="muted">
            The observability stack is optional for local development. Start it with{" "}
            <code>make up-observability</code>.
          </p>
        </div>
      </div>
      <section className="status-grid">
        {links.map(([title, href, detail]) => (
          <a className="card linked-card" href={href} key={title}>
            <div className="card-body stack">
              <div className="panel-title">
                <h2>{title}</h2>
                <span className="badge">local</span>
              </div>
              <p className="muted">{detail}</p>
              <code>{href}</code>
            </div>
          </a>
        ))}
      </section>
    </main>
  );
}
