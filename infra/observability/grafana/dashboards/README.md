# Grafana Dashboards

Phase 14 provisions dashboards as code. Grafana loads this directory through
`infra/observability/grafana/provisioning/dashboards/dashboards.yml`.

Dashboards:

- `realtime-ux.json`: first audio, turn latency, STT/TTS, event lag, interruptions.
- `browser-reliability.json`: browser action success, screen reads, policy blocks, recovery.
- `agent-quality.json`: LLM latency, validation failures, fallbacks, recipe progress.
- `infrastructure-health.json`: HTTP, Redis/DB placeholders, event publishing, queue depth.
- `cost-usage.json`: model invocations, tokens, audio seconds, embedding vectors, CRM exports.
- `session-debug.json`: log and trace-oriented session debugging without Prometheus session labels.
- `latency-budget.json`: budget checks, violations, excess latency, compliance.

Validate locally:

```bash
make obs-dashboards-validate
```
