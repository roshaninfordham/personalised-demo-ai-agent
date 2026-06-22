# Unsafe Production Config Runbook

Symptoms: service fails startup with `Unsafe production configuration`.

Commands:

```bash
kubectl -n live-demo-agent describe pod <pod>
kubectl -n live-demo-agent logs <pod>
kubectl -n live-demo-agent get configmap live-demo-agent-config -o yaml
```

Mitigation: set safe values:

- `ALLOW_LOCAL_PRODUCT_URLS=false`
- `ALLOW_DESTRUCTIVE_ACTIONS=false`
- `BROWSER_CHROMIUM_NO_SANDBOX=false`
- `BROWSER_BLOCK_EXTERNAL_NAVIGATION=true`
- non-default `JWT_SECRET`, `SESSION_SECRET`, `REDACTION_HASH_SECRET`

Rollback: restore previous ConfigMap/Secret and restart affected deployments.

Prevention: run `make ci-local` and `make k8s-validate` before deploy.
