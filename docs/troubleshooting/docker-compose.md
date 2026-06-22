# Docker Compose Troubleshooting

## Symptom

Compose fails to build, services restart, or dependencies never become healthy.

## Likely Causes

- Docker daemon not running.
- Port conflict.
- Stale volumes.
- Missing `.env`.
- Healthcheck failure.

## Quick Checks

```bash
docker compose config
docker compose ps
docker compose logs --tail=200
```

## Logs and Metrics

Use service logs first. Observability is optional and may not be running.

## Fix

```bash
cp .env.example .env
docker compose down
docker compose up --build
```

For a full local reset:

```bash
docker compose down -v
rm -rf .local/test-artifacts .local/mock-crm-exports
docker compose up --build
```

## Prevention

Keep `.env.example` as the local source of truth and avoid changing Compose service ports unless necessary.
