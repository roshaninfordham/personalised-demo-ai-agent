# Security, Deployment, and Production Hardening

Phase 16 packages the platform for staging and production without changing product behavior.

## Production Topology

```mermaid
flowchart TB
    Ingress["Ingress"] --> Web["web"]
    Web --> API["api"]
    API --> Browser["browser-runtime"]
    API --> Agent["agent-runtime"]
    API --> Learner["learner-worker"]
    API --> PostDemo["post-demo-worker"]
    API --> Redis["Redis"]
    API --> Postgres["Managed Postgres + pgvector"]
    Browser --> ObjectStore["S3-compatible object storage"]
    Agent --> Redis
    Learner --> Redis
    PostDemo --> Redis
    OTel["OpenTelemetry Collector"] --> Prometheus["Prometheus"]
    OTel --> Loki["Loki"]
    OTel --> Jaeger["Jaeger"]
```

Managed Postgres and managed Redis are recommended for production. The in-cluster Redis
manifest is suitable for staging or self-managed installations.

## Container Hardening

```mermaid
flowchart LR
    Dockerfile["Multi-stage Dockerfile"] --> Runtime["Minimal runtime stage"]
    Runtime --> NonRoot["USER 10001:10001"]
    Runtime --> NoEnv["No .env copied"]
    Runtime --> Stdout["Logs to stdout/stderr"]
    K8s["Kubernetes"] --> ReadOnly["readOnlyRootFilesystem"]
    K8s --> DropCaps["capabilities.drop=ALL"]
    K8s --> NoEsc["allowPrivilegeEscalation=false"]
    ReadOnly --> EmptyDir["Explicit /tmp and cache emptyDir"]
```

## Browser Sandboxing

```mermaid
sequenceDiagram
    participant API
    participant Browser as Browser Runtime
    participant Context as Playwright Context
    participant Page
    participant Product

    API->>Browser: create session with allowed domains
    Browser->>Context: isolated context per session
    Context->>Page: install guards
    Page->>Product: request allowed resources only
    Product-->>Page: screen state
    Browser->>Context: clear cookies/permissions on close
```

Production startup fails if Chromium no-sandbox, local product URLs, downloads, uploads,
payment pages, destructive actions, or external navigation are enabled.

## Secrets

```mermaid
flowchart TB
    Local["local .env"] --> EnvProvider["EnvSecretProvider"]
    K8sSecret["Kubernetes Secret"] --> K8sProvider["KubernetesSecretProvider"]
    Future["AWS/GCP/Azure/Vault/External Secrets"] --> Interface["SecretProvider protocol"]
    EnvProvider --> App["Services"]
    K8sProvider --> App
    Interface --> App
```

Phase 16 loads secrets at startup. Rotation requires a rolling restart until live reload is
implemented.

## CI/CD

```mermaid
flowchart LR
    PR["Pull request"] --> CI["contracts/lint/type/test"]
    CI --> Docker["Docker build"]
    Docker --> Scans["secret/dependency/image/k8s scans"]
    Main["main"] --> Staging["deploy staging"]
    Tag["release tag/manual"] --> Approval["production approval"]
    Approval --> Prod["deploy production"]
    Prod --> Smoke["smoke tests"]
```

## Autoscaling

```mermaid
flowchart TB
    API["api"] --> HPA1["HPA CPU/memory"]
    Web["web"] --> HPA2["HPA CPU/memory"]
    Agent["agent-runtime"] --> HPA3["HPA active voice sessions + CPU"]
    Browser["browser-runtime"] --> HPA4["HPA active browser sessions + memory"]
    Learner["learner-worker"] --> KEDA1["KEDA Redis stream backlog"]
    PostDemo["post-demo-worker"] --> KEDA2["KEDA Redis stream backlog"]
```

Scale-down is stabilized for hot-path services. Agent and browser pods use preStop hooks and
termination grace periods so active sessions can drain.

## Rollback

```mermaid
flowchart LR
    Detect["Detect regression"] --> Freeze["Freeze production deploys"]
    Freeze --> Rollback["kubectl rollout undo"]
    Rollback --> Smoke["Smoke checks"]
    Smoke --> DB["Manual DB review if schema involved"]
```

Database migrations are forward-only by default. Automatic DB downgrades are not performed.
