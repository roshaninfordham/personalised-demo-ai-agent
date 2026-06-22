# API Service

`services/api` is the backend control plane. It owns product/session APIs, session orchestration, recipe APIs, post-demo intelligence, persistence-facing repositories, event publishing, audit integration, and frontend-safe join/readiness state.

It does not run Playwright directly, run the Pipecat pipeline directly, or execute LLM decisions directly.

## Ownership

```mermaid
flowchart TB
    API["services/api"]
    Products["Products + guidance"]
    Sessions["Demo sessions"]
    Orchestrator["Session orchestrator"]
    Recipes["Recipe validation/compile/progress"]
    Audit["Audit logging"]
    PostDemo["Post-demo intelligence"]
    Events["Frontend event gateway"]
    Repos["Postgres repositories"]
    Redis["Redis live state"]

    API --> Products
    API --> Sessions
    API --> Orchestrator
    API --> Recipes
    API --> Audit
    API --> PostDemo
    API --> Events
    API --> Repos
    API --> Redis
```

## Orchestration Boundary

```mermaid
flowchart LR
    Web["Frontend"] --> API["API routes"]
    API --> Orch["SessionOrchestrator"]
    Orch --> BrowserClient["BrowserRuntimeClient"]
    Orch --> AgentClient["AgentRuntimeClient"]
    Orch --> LearnerClient["LearnerWorkerClient"]
    Orch --> ProviderHealth["ProviderHealthClient"]
    Orch --> DB["Postgres"]
    Orch --> Redis["Redis"]
    BrowserClient --> Browser["browser-runtime"]
    AgentClient --> Agent["agent-runtime"]
    LearnerClient --> Learner["learner-worker"]
```

The orchestrator coordinates services through internal clients. It records resources durably and never reaches into runtime internals.

## Main API Session Flow

```mermaid
sequenceDiagram
    participant Web
    participant API
    participant Orch as SessionOrchestrator
    participant Browser
    participant Agent
    participant Learner
    participant Store as Postgres/Redis

    Web->>API: POST /demo-sessions
    API->>Store: create demo session
    Web->>API: POST /demo-sessions/{id}/prewarm
    API->>Orch: prewarm_session
    Orch->>Browser: create/navigate/read screen
    Orch->>Agent: create voice session
    Orch->>Learner: enqueue learner job
    Orch->>Store: resources + readiness
    API-->>Web: readiness + join config
    Web->>API: POST /demo-sessions/{id}/start
    API->>Orch: start_live_session
    API-->>Web: join config
    Web->>API: POST /demo-sessions/{id}/end
    API->>Orch: shutdown_session
```

## Durable Tables Added For Orchestration

```mermaid
erDiagram
    demo_sessions ||--o{ session_orchestration_runs : has
    demo_sessions ||--o{ session_resource_allocations : owns
    demo_sessions ||--o{ session_lifecycle_events : emits

    session_orchestration_runs {
      uuid orchestration_run_id
      uuid organization_id
      uuid session_id
      text run_type
      text status
      text trace_id
    }

    session_resource_allocations {
      uuid resource_allocation_id
      uuid organization_id
      uuid session_id
      text resource_type
      text resource_id
      text status
    }

    session_lifecycle_events {
      uuid session_lifecycle_event_id
      uuid organization_id
      uuid session_id
      text event_type
      text severity
      text trace_id
    }
```

## Key Modules

| Module | Purpose |
| --- | --- |
| `orchestration/session_orchestrator.py` | Main prewarm/start/recover/shutdown coordinator |
| `orchestration/readiness.py` | Deterministic readiness scoring |
| `orchestration/resource_registry.py` | Durable resource allocation state |
| `orchestration/orchestration_locks.py` | Redis owner locks with safe release |
| `orchestration/idempotency.py` | Duplicate operation protection |
| `orchestration/browser_agent_sync.py` | Speech/action/screen sync state |
| `clients/*_client.py` | Bounded internal service clients |
| `repositories/session_*` | Phase 12 durable state repositories |
| `post_demo/*` | Phase 13 evidence-backed insight, summary, and CRM export modules |

## Post-Demo Intelligence Boundary

```mermaid
flowchart TB
    End["Session ended"] --> Run["POST /post-demo/run"]
    Run --> Evidence["Load bounded evidence"]
    Evidence --> Insights["Extract lead insights"]
    Evidence --> Features["Track features shown"]
    Insights --> Summary["Generate lead summary"]
    Features --> Summary
    Summary --> CRM["Optional mock CRM export"]
    Summary --> DB["lead_summaries"]
    Insights --> InsightDB["lead_insights"]
    Features --> FeatureDB["features_shown"]
    CRM --> ExportDB["crm_exports"]
```

The post-demo path is cold-path only. It validates evidence IDs, redacts text before summaries and CRM payloads, and defaults CRM export to the mock dry-run adapter.

## State And Event Safety

```mermaid
flowchart TD
    Raw["Internal result"] --> Redact["Redact metadata"]
    Redact --> Event["Publish typed event"]
    Redact --> DB["Persist durable event/resource"]
    Event --> Frontend["Frontend reducer"]
```

Events must not include provider secrets, raw prompts, raw audio, screenshots/base64, cookies, or tokens.

## Verification

```bash
make orchestration-test
make orchestration-test-integration
make orchestration-smoke
make post-demo-test
make post-demo-test-integration
```
