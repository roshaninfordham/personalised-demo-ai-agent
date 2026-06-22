# Recovery Mode Runbook

## Symptoms

The browser screen changed unexpectedly, an action ID is stale, or policy detects a high-risk screen.

## Dashboards

- browser reliability;
- session debug;
- latency budget.

## Logs and Traces

```bash
docker compose logs api --tail=200
docker compose logs browser-runtime --tail=200
```

Look for:

```text
session.recovery.started
browser.screen.updated
recovery_failed
policy_blocked
```

## Commands

```bash
curl -s $API_URL/api/v1/demo-sessions/<session_id>/orchestration-state
```

## Mitigation

Recovery decision order:

1. pause risky actions;
2. read current screen;
3. refresh safe actions;
4. go back only when safe;
5. navigate home only when safe;
6. ask user if confidence is low;
7. end or degrade after max attempts.

## Prevention

Keep recipes conservative and make fallback strategies explicit.
