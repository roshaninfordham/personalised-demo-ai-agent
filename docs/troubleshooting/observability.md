# Observability Troubleshooting

## Symptom

Grafana dashboards are empty, Prometheus is down, traces are missing, or logs are not queryable.

## Likely Causes

- Observability profile not started.
- OTel collector unavailable.
- Service exporters disabled.
- Dashboard provisioning path wrong.
- Metrics endpoint not scraped yet.

## Quick Checks

```bash
docker compose --profile observability ps
curl -s http://localhost:9090/-/healthy
curl -s http://localhost:3001/api/health
docker compose logs otel-collector --tail=200
```

## Logs and Metrics

Check:

- collector logs;
- Prometheus targets;
- Grafana datasource status;
- application stdout JSON logs.

## Fix

```bash
docker compose --profile observability up --build
make obs-dashboards-validate
```

If collector is unavailable, application services should continue. Observability failures should not crash live sessions.

## Prevention

Keep observability optional for local low-resource mode and enabled for debugging sessions.
