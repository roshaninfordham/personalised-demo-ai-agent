# System Design

This document explains the system as it exists through Phase 12. It is intentionally implementation-oriented: each box maps to a package, service, table group, Redis key group, or runtime boundary in the repository.

## C4-Style Container View

```mermaid
flowchart TB
    subgraph Client["Client"]
        Web["apps/web<br/>Next.js live demo UI"]
    end

    subgraph Backend["Backend Services"]
        API["services/api<br/>FastAPI, session orchestration, recipes, products"]
        Agent["services/agent_runtime<br/>Pipecat voice runtime, agent brain"]
        Browser["services/browser_runtime<br/>Playwright browser execution"]
        Learner["services/learner_worker<br/>Product learner and demo graph"]
        TTS["services/tts_service<br/>TTS service boundary"]
    end

    subgraph Shared["Shared Packages"]
        Contracts["packages/contracts<br/>JSON schemas + generated models"]
        BackendCommon["packages/backend_common<br/>AI providers, policy engines"]
        Policies["packages/policies<br/>Policy rules + generated constants"]
    end

    subgraph Data["Data Plane"]
        Postgres["Postgres<br/>durable relational state + pgvector"]
        Redis["Redis<br/>live state, locks, streams"]
        ObjectStore["MinIO/S3<br/>artifacts"]
    end

    Web --> API
    API --> Agent
    API --> Browser
    API --> Learner
    Agent --> Browser
    Learner --> Browser
    API --> Redis
    Agent --> Redis
    Browser --> Redis
    Learner --> Redis
    API --> Postgres
    Agent --> Postgres
    Learner --> Postgres
    Browser --> ObjectStore
    API --> Contracts
    Agent --> Contracts
    Browser --> Contracts
    Learner --> Contracts
    API --> BackendCommon
    Agent --> BackendCommon
    Learner --> BackendCommon
    API --> Policies
    Agent --> Policies
    Browser --> Policies
    Learner --> Policies
```

## Hot Path Versus Cold Path

```mermaid
flowchart LR
    subgraph Hot["Hot Path: live user turn"]
        U["User speaks"] --> STT["STT final"]
        STT --> Context["Bounded context builder"]
        Context --> LLM["TextGenerationProvider"]
        LLM --> Validate["Strict decision validator"]
        Validate --> TTS["TTS begins"]
        Validate --> Router["Tool router"]
        Router --> Browser["Browser runtime"]
        Browser --> Screen["Screen update"]
    end

    subgraph Cold["Cold Path: background learning"]
        URL["Product URL"] --> Learner["Learner worker"]
        Learner --> Summary["Screen summaries"]
        Summary --> Graph["Demo graph"]
        Graph --> Route["Generated route"]
        Summary --> Chunks["Knowledge chunks"]
        Chunks --> Vector["pgvector retrieval"]
    end

    Vector -. "bounded facts later" .-> Context
    Graph -. "safe graph hints later" .-> Context
```

Invariant: cold-path work can improve future context, but first audio and live agent turns do not wait for learner completion.

## Session Orchestration State Machine

```mermaid
stateDiagram-v2
    [*] --> created
    created --> prewarming: start_prewarm
    prewarming --> waiting_for_user: prewarm_ready
    prewarming --> degraded_ready: partial_prewarm_ready
    prewarming --> failed: prewarm_fatal_failure
    waiting_for_user --> live: user_joined
    degraded_ready --> live: user_joined
    live --> recovery: unexpected_browser_or_agent_state
    recovery --> live: recovered
    recovery --> live_degraded: partially_recovered
    recovery --> ending: unrecoverable_or_user_ends
    live --> ending: user_ends_or_timeout
    live_degraded --> ending: user_ends_or_timeout
    ending --> finalizing: resources_stopped
    finalizing --> completed: finalization_success
    finalizing --> completed_with_warnings: nonfatal_finalization_failure
    finalizing --> failed: fatal_finalization_failure
```

Durable session statuses remain compatible with existing API contracts; runtime-only states are stored in orchestration state and frontend events.

## Prewarm DAG

```mermaid
flowchart TD
    Load["Load demo session"] --> Compile["Compile recipe if present"]
    Load --> BrowserCreate["Create browser session"]
    BrowserCreate --> Navigate["Navigate to start URL"]
    Navigate --> ReadScreen["Read first screen"]
    ReadScreen --> RedisScreen["Write screen + safe actions to Redis"]
    ReadScreen --> ScreenEvent["Publish browser.screen.updated"]

    Load --> VoiceCreate["Create voice session"]
    VoiceCreate --> Join["Get join config"]

    Load --> LLM["Warm LLM provider"]
    Load --> STT["Warm STT provider"]
    Load --> TTS["Warm TTS provider"]

    Load --> LearnerRun["Create learner run"]
    LearnerRun --> LearnerJob["Enqueue learner job"]

    Compile --> Readiness["Compute readiness"]
    RedisScreen --> Readiness
    Join --> Readiness
    LLM --> Readiness
    STT --> Readiness
    TTS --> Readiness
    LearnerJob --> Readiness
```

Required browser work gates readiness. Provider warmup and learner enqueue are bounded optional contributors unless settings require otherwise.

## Agent Turn Control Flow

```mermaid
sequenceDiagram
    participant User
    participant Agent as Agent Runtime
    participant Context as Context Builder
    participant LLM as TextGenerationProvider
    participant Policy as Policy/Validator
    participant TTS
    participant Browser as Browser Runtime
    participant Store as Redis/Postgres

    User->>Agent: final transcript
    Agent->>Context: build compact context
    Context->>Store: current screen, safe actions, recipe, persona, knowledge
    Context-->>Agent: bounded source-attributed context
    Agent->>LLM: system prompt + context + JSON schema
    LLM-->>Policy: structured decision
    Policy-->>Agent: validated decision or fallback
    Agent->>TTS: stream spoken_response
    Agent->>Browser: route safe action_id if present
    Browser-->>Store: action event + new screen
```

The LLM never receives raw browser authority, raw selectors, arbitrary JavaScript, cookies, screenshots, or unbounded DOM.

## Policy Enforcement Stack

```mermaid
flowchart TD
    Action["Proposed browser/product action"] --> Normalize["Normalize bounded fields"]
    Normalize --> RBAC["RBAC permission check"]
    RBAC --> HardBlock["Global hard-block rules"]
    HardBlock --> RecipeNever["Recipe never_click"]
    RecipeNever --> Domain["Allowed domain policy"]
    Domain --> Field["Form field policy"]
    Field --> Risk["Risk score"]
    Risk --> Decision{"Decision"}
    Decision -->|low/allowed| Execute["Browser runtime validates again"]
    Decision -->|high| Confirm["Confirmation required"]
    Decision -->|blocked| Stop["Do not execute"]
```

Recipe policy can make execution stricter, but cannot bypass global hard blocks.

## Data Persistence Map

```mermaid
erDiagram
    organizations ||--o{ products : owns
    organizations ||--o{ demo_sessions : owns
    products ||--o{ demo_sessions : has
    demo_sessions ||--o{ session_orchestration_runs : has
    demo_sessions ||--o{ session_resource_allocations : has
    demo_sessions ||--o{ session_lifecycle_events : emits
    products ||--o{ product_learning_runs : learns
    products ||--o{ screen_snapshots : observes
    products ||--o{ demo_graph_edges : links
    products ||--o{ generated_demo_routes : suggests
    products ||--o{ knowledge_chunks : indexes
    products ||--o{ demo_recipes : configures
    demo_recipes ||--o{ compiled_demo_recipes : compiles
    demo_sessions ||--o{ recipe_step_progress : tracks
    organizations ||--o{ audit_logs : audits
```

## Event Flow

```mermaid
flowchart LR
    API["API / orchestrator"] --> Streams["Redis Streams"]
    Agent["Agent runtime"] --> Streams
    Browser["Browser runtime"] --> Streams
    Learner["Learner worker"] --> Streams
    Streams --> Gateway["API event gateway"]
    Gateway --> Web["Frontend reducer"]
    Web --> UI["Readiness, browser, transcript, learning panels"]
```

Frontend-visible events are typed and redacted. They carry status, resource IDs, safe messages, counts, and trace IDs, not prompts, provider secrets, raw audio, cookies, screenshots, or tokens.

## Deployment View

```mermaid
flowchart TB
    subgraph Compose["docker-compose.yml"]
        API["api"]
        Agent["agent-runtime"]
        Browser["browser-runtime"]
        Learner["learner-worker"]
        Web["web"]
        Postgres["postgres"]
        Redis["redis"]
        MinIO["minio"]
    end

    API --> Postgres
    API --> Redis
    API --> Agent
    API --> Browser
    API --> Learner
    Browser --> Redis
    Browser --> MinIO
    Agent --> Redis
    Agent --> Postgres
    Learner --> Redis
    Learner --> Postgres
    Learner --> Browser
    Web --> API
```

The API treats runtime dependencies as orchestration resources. Readiness can degrade instead of forcing all optional dependencies to block local boot.

