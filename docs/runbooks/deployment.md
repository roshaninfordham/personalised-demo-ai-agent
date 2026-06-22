# Deployment Runbook

```mermaid
sequenceDiagram
    participant CI
    participant Registry
    participant K8s
    participant Smoke

    CI->>Registry: build/tag images with git SHA
    CI->>K8s: apply ConfigMaps/Secrets
    CI->>K8s: run db-migrate job
    CI->>K8s: rollout API/browser/agent/workers/web
    CI->>Smoke: health/readiness checks
```

Symptoms: rollout stalls, pods crashloop, smoke test fails.

Dashboards: infrastructure health, latency budget, browser reliability.

Commands:

```bash
make k8s-render
scripts/deploy/deploy_staging.sh
kubectl -n live-demo-agent get pods
kubectl -n live-demo-agent rollout status deployment/api
```

Mitigation: pause production, inspect events/logs, rollback application deployments if schema is compatible.

Rollback: `scripts/deploy/rollback.sh production`.

Prevention: deploy staging first, keep migrations forward-compatible, run `make ci-local`.
