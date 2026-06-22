# Rollback Runbook

Symptoms: elevated 5xx, failed prewarm, browser crash loops, latency budget violations after deploy.

Commands:

```bash
scripts/deploy/rollback.sh staging
scripts/deploy/rollback.sh production
kubectl -n live-demo-agent rollout history deployment/api
```

Mitigation: rollback deployments first. Do not automatically downgrade database schema.

Rollback: use Kubernetes ReplicaSet rollback; run manual DB recovery only from a reviewed migration plan.

Prevention: forward-compatible migrations and staging smoke before production approval.
