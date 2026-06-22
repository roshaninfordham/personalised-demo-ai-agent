# High First-Audio Latency Runbook

Symptoms: `live_demo_first_audio_latency_seconds` p95 above budget, user hears silence after a turn.

Dashboards: realtime UX, agent quality, latency budget, cost/usage.

Commands:

```bash
kubectl -n live-demo-agent logs deploy/agent-runtime --tail=200 | grep latency_budget.violation
kubectl -n live-demo-agent logs deploy/api --tail=200 | grep turn
```

Mitigation: check provider latency, switch provider routing if configured, reduce context size, disable optional retrieval.

Rollback: revert agent-runtime deployment if regression followed a release.

Prevention: keep Phase 15 latency evals and Phase 14 budgets in CI.
