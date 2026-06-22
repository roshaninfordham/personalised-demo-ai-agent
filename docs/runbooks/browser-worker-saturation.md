# Browser Worker Saturation Runbook

Symptoms: `browser_session_limit_reached`, prewarm delays, browser-runtime memory near limit.

Dashboards: browser reliability, infrastructure health, latency budget.

Commands:

```bash
kubectl -n live-demo-agent top pods -l app.kubernetes.io/name=browser-runtime
kubectl -n live-demo-agent logs deploy/browser-runtime --tail=200
kubectl -n live-demo-agent scale deployment/browser-runtime --replicas=5
```

Mitigation: increase browser replicas, lower max concurrent sessions per pod, shed low-priority prewarms.

Rollback: restore previous HPA and resource limits if new config caused instability.

Prevention: tune from Phase 15 load tests; keep readiness false when a pod is full.
