# Failed Prewarm Runbook

Symptoms: sessions stuck in `prewarming`, browser first screen missing, degraded readiness.

Dashboards: realtime UX, browser reliability, session debug.

Commands:

```bash
kubectl -n live-demo-agent logs deploy/api --tail=200 | grep session.prewarming
kubectl -n live-demo-agent logs deploy/browser-runtime --tail=200
kubectl -n live-demo-agent get events --sort-by=.lastTimestamp
```

Mitigation: verify browser-runtime health, domain allowlist, object storage credentials, Redis connectivity.

Rollback: rollback API/browser-runtime if failures correlate with deploy.

Prevention: staging prewarm smoke and browser sandbox tests.
