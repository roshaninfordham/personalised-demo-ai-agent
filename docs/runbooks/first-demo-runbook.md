# First Demo Runbook

## Symptoms

You need to run the first local demo from a clean checkout.

## Dashboards

Observability is optional for the first run. Use service health first.

## Commands

```bash
cp .env.example .env
make up
make health
```

Open:

```bash
make open
```

## Mitigation

If a service fails, switch to [troubleshooting.md](../troubleshooting/troubleshooting.md).

## Prevention

Keep fake providers as the default first-run mode.
