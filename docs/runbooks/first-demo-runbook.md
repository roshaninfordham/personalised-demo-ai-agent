# First Demo Runbook

## Symptoms

You need to run the first local demo from a clean checkout.

## Dashboards

Observability is optional for the first run. Use service health first.

## Commands

```bash
cp .env.example .env
pnpm install
uv sync --all-packages
docker compose up --build
curl -s http://localhost:8000/healthz
curl -s http://localhost:8200/healthz
curl -s http://localhost:8300/healthz
```

Open:

```text
http://localhost:3000
```

## Mitigation

If a service fails, switch to [troubleshooting.md](../troubleshooting/troubleshooting.md).

## Prevention

Keep fake providers as the default first-run mode.
