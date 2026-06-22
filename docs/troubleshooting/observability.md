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
curl -s $NEXT_PUBLIC_PROMETHEUS_URL/-/healthy
curl -s $NEXT_PUBLIC_GRAFANA_URL/api/health
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
make up-observability
make obs-dashboards-validate
```

If collector is unavailable, application services should continue. Observability failures should not crash live sessions.

## Prevention

Keep observability optional for local low-resource mode and enabled for debugging sessions.
