# Debugging a Live Session

## Symptoms

The session is slow, action execution fails, transcript is missing, or UI state looks stale.

## Dashboards

- realtime UX;
- browser reliability;
- session debug;
- latency budget.

## Logs and Traces

```bash
docker compose logs api --tail=200
docker compose logs agent-runtime --tail=200
docker compose logs browser-runtime --tail=200
docker compose exec redis redis-cli keys 'live_demo:session:*'
```

## Commands

```bash
curl -s http://localhost:8000/api/v1/demo-sessions/<session_id>/state
curl -s http://localhost:8000/api/v1/demo-sessions/<session_id>/orchestration-state
```

## Mitigation

- If browser state is unexpected, trigger screen refresh/recovery.
- If provider is slow, switch to fake provider mode.
- If Redis state is stale, end the session and verify cleanup.

## Prevention

Use bounded recovery attempts and latency budget alerts.
