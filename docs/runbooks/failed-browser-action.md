# Failed Browser Action Runbook

## Symptoms

The cursor moves but the action does not complete, or the UI does not update after a click.

## Dashboards

- browser reliability dashboard;
- latency budget dashboard;
- session debug logs.

## Logs and Traces

```bash
docker compose logs browser-runtime --tail=200
docker compose logs api --tail=100
```

Look for:

```text
browser.action.failed
policy_blocked
screen_read_timeout
recovery_failed
```

## Commands

```bash
curl -s http://localhost:8200/healthz
curl -s http://localhost:8200/readyz
```

## Mitigation

1. Read current screen.
2. Refresh safe actions.
3. Retry only if policy still allows the action.
4. Ask the user or degrade if recovery attempts are exhausted.

## Rollback

End the session. Shutdown should close the browser context and release resources.

## Prevention

Prefer label-based recipes, avoid raw selectors, and test dynamic SPA flows with fixture apps.
