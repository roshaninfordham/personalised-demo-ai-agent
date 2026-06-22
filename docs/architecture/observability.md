# Observability

Phase 14 adds local open-source observability: OpenTelemetry traces, Prometheus metrics, structured JSON logs, Grafana dashboards, and latency budgets.

```mermaid
flowchart TB
    Services["API / Agent / Browser / Learner / Post-Demo"]
    Trace["Trace spans"]
    Metric["Metrics"]
    Log["JSON logs"]
    Collector["OTel Collector"]
    Prom["Prometheus"]
    Loki["Loki"]
    Jaeger["Jaeger"]
    Grafana["Grafana"]

    Services --> Trace
    Services --> Metric
    Services --> Log
    Trace --> Collector
    Metric --> Collector
    Log --> Collector
    Collector --> Prom
    Collector --> Loki
    Collector --> Jaeger
    Prom --> Grafana
    Loki --> Grafana
    Jaeger --> Grafana
```

Run:

```bash
make up-observability
```

Dashboards:

- realtime UX;
- browser reliability;
- agent quality;
- infrastructure health;
- cost/usage;
- session debug;
- latency budget.

No prompt text, raw transcript, screenshots, audio, cookies, provider keys, or API keys should appear in telemetry.
