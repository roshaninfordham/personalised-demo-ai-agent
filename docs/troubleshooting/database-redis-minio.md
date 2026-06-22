# Database, Redis, and MinIO

## Symptom

API readiness fails, events do not arrive, screenshots are missing, or migrations fail.

## Likely Causes

- Postgres is unhealthy.
- Redis is unavailable.
- MinIO bucket cannot be created.
- Migrations not applied.
- Host-side env points at container DNS instead of localhost.

## Quick Checks

```bash
docker compose ps postgres redis minio
docker compose exec postgres pg_isready -U demo_agent -d demo_agent
docker compose exec redis redis-cli ping
curl -s http://localhost:9000/minio/health/live
make db-current
```

## Logs and Metrics

```bash
docker compose logs postgres --tail=100
docker compose logs redis --tail=100
docker compose logs minio --tail=100
docker compose logs api --tail=100
```

## Fix

```bash
docker compose up -d postgres redis minio
make db-upgrade
```

If local state is corrupted:

```bash
docker compose down -v
docker compose up -d postgres redis minio
make db-upgrade
```

## Prevention

Keep host-side `.env` URLs on `localhost`. Compose overrides service URLs inside containers.
