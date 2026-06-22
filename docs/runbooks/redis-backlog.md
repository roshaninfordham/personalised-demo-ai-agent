# Redis Backlog Runbook

Symptoms: learner/post-demo jobs delayed, KEDA scales workers, Redis memory grows.

Commands:

```bash
kubectl -n live-demo-agent exec statefulset/redis -- redis-cli XLEN live_demo:stream:learner:jobs
kubectl -n live-demo-agent exec statefulset/redis -- redis-cli XLEN live_demo:stream:post_demo:jobs
kubectl -n live-demo-agent get scaledobject
```

Mitigation: scale workers, pause non-critical enqueue paths, inspect dead-letter streams.

Rollback: rollback worker deployment if backlog started after release.

Prevention: queue-depth autoscaling and bounded job payloads.
