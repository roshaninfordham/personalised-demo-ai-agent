# Pod Security Standards

The `live-demo-agent` namespace enforces Kubernetes Pod Security `restricted`.

```mermaid
flowchart LR
    Namespace["Namespace labels"] --> Restricted["restricted enforce/audit/warn"]
    Restricted --> Workloads["Non-root workloads"]
    Workloads --> RuntimeDefault["RuntimeDefault seccomp"]
    Workloads --> DropCaps["drop ALL capabilities"]
    Workloads --> NoPrivEsc["allowPrivilegeEscalation=false"]
```

Browser runtime uses writable `emptyDir` mounts for `/tmp`, `/app/.cache`, and
`/dev/shm`. It is not privileged and must not run with `BROWSER_CHROMIUM_NO_SANDBOX=true`
in production.
