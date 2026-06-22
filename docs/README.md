# Documentation Hub

This directory is the current architecture and operations map for the live AI product-demo agent platform.

The platform has two execution paths:

- Hot path: user speech, compact grounded context, agent decision, TTS, and safe browser actions.
- Cold path: learner jobs, product graph updates, recipe generation, embeddings, summaries, and post-session work.

## Reading Map

| Area | Document |
| --- | --- |
| System architecture | [architecture/system-design.md](architecture/system-design.md) |
| User and agent flows | [flows/user-agent-flow.md](flows/user-agent-flow.md) |
| Local development and verification | [operations/local-development.md](operations/local-development.md) |
| Phase 0 foundation | [../architecture/README.md](../architecture/README.md) |
| Shared contracts | [../packages/contracts/README.md](../packages/contracts/README.md) |
| Shared policy package | [../packages/policies/README.md](../packages/policies/README.md) |

## Product Capability Map

```mermaid
mindmap
  root((Live Demo Agent))
    Realtime Demo
      Voice runtime
      Grounded agent brain
      Browser action routing
      Frontend live UI
    Safety
      Policy engine
      RBAC
      Audit logs
      Redaction
      Recipe constraints
    Learning
      Product learner worker
      Demo graph
      Screen matching
      Knowledge chunks
      pgvector retrieval
    Reliability
      Session orchestrator
      Prewarming
      Recovery
      Shutdown
      Resource registry
    Authoring
      Demo recipes
      Text guidance conversion
      Compiled hot-path plan
      Progress tracking
```

## Runtime System

```mermaid
flowchart TB
    User["User / prospect"]
    Web["apps/web<br/>Live demo UI"]
    API["services/api<br/>Backend + orchestrator"]
    Agent["services/agent_runtime<br/>Pipecat + agent brain"]
    Browser["services/browser_runtime<br/>Playwright execution authority"]
    Learner["services/learner_worker<br/>Cold-path product learner"]
    TTS["services/tts_service<br/>Optional TTS boundary"]
    Contracts["packages/contracts<br/>Generated DTOs"]
    Policies["packages/policies<br/>Generated rules"]
    Common["packages/backend_common<br/>AI + policy implementation"]
    Postgres["Postgres + pgvector"]
    Redis["Redis live state + streams"]
    MinIO["MinIO / S3 artifacts"]

    User --> Web
    Web --> API
    API --> Agent
    API --> Browser
    API --> Learner
    Agent --> Browser
    Agent --> Redis
    Browser --> Redis
    Browser --> MinIO
    Learner --> Browser
    Learner --> Postgres
    Learner --> Redis
    API --> Postgres
    API --> Redis
    TTS --> Agent

    API --> Contracts
    Agent --> Contracts
    Browser --> Contracts
    Learner --> Contracts
    API --> Policies
    Agent --> Policies
    Browser --> Policies
    Learner --> Policies
    API --> Common
    Agent --> Common
    Learner --> Common
```

## Main Session Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Prewarming: API prewarm/start
    Prewarming --> WaitingForUser: required resources ready
    Prewarming --> DegradedReady: optional resource failed
    Prewarming --> Failed: required resource failed
    WaitingForUser --> Live: transport connected
    DegradedReady --> Live: transport connected
    Live --> Recovery: unexpected state
    Recovery --> Live: recovered
    Recovery --> LiveDegraded: partial recovery
    Recovery --> Ending: unrecoverable/user ends
    Live --> Ending: user ends/timeout
    LiveDegraded --> Ending: user ends/timeout
    Ending --> Finalizing: resources stopped
    Finalizing --> Completed: success
    Finalizing --> CompletedWithWarnings: nonfatal cleanup issue
    Finalizing --> Failed: fatal finalization issue
```

## Source Of Truth Boundaries

```mermaid
flowchart LR
    Contracts["Contract schemas"] --> Generated["Generated TS/Python models"]
    PolicyRules["Policy rule JSON"] --> PolicyGenerated["Generated TS/Python policy constants"]
    DB["Postgres"] --> Durable["Durable state"]
    Redis["Redis"] --> Hot["Hot session state"]

    Generated --> API["API"]
    Generated --> Web["Web"]
    Generated --> Agent["Agent runtime"]
    Generated --> Browser["Browser runtime"]
    PolicyGenerated --> API
    PolicyGenerated --> Agent
    PolicyGenerated --> Browser
    PolicyGenerated --> Learner["Learner worker"]
```

Rules:

- Contract schemas are the DTO source of truth.
- Policy JSON is the policy rule source of truth.
- Postgres owns durable session, graph, recipe, audit, and knowledge records.
- Redis owns bounded live state, locks, streams, and hot-path caches.
- Browser runtime is the final browser execution authority.
- The LLM proposes intent; policy and browser runtime decide execution.

## Service READMEs

| Service | README |
| --- | --- |
| API / orchestrator | [../services/api/README.md](../services/api/README.md) |
| Agent runtime | [../services/agent_runtime/README.md](../services/agent_runtime/README.md) |
| Browser runtime | [../services/browser_runtime/README.md](../services/browser_runtime/README.md) |
| Learner worker | [../services/learner_worker/README.md](../services/learner_worker/README.md) |
| Frontend | [../apps/web/README.md](../apps/web/README.md) |
