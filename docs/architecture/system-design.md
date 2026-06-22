# System Design

Live Demo Agent is a realtime AI sales-engineer runtime. It opens a real product URL in an isolated controlled browser, learns the product screen, speaks with the user over voice, moves a synthetic cursor, executes safe browser actions, answers questions grounded in the live UI and approved knowledge, and generates post-demo sales intelligence.

## System Overview

```mermaid
flowchart TB
    User["User / Prospect"]

    subgraph Frontend["Frontend: Next.js"]
        DemoForm["Demo Start Form"]
        LiveUI["Live Demo UI"]
        BrowserViewport["Browser Viewport"]
        CursorOverlay["Cursor Overlay"]
        CallPanel["Call Panel"]
        TranscriptPanel["Transcript Panel"]
        DebugPanel["Latency Debug Panel"]
    end

    subgraph API["API Backend: FastAPI"]
        ProductAPI["Product APIs"]
        SessionAPI["Session APIs"]
        RecipeAPI["Recipe APIs"]
        Orchestrator["Session Orchestrator"]
        EventGateway["Event Gateway"]
    end

    subgraph Agent["Agent Runtime: Pipecat"]
        VoicePipeline["Voice Pipeline"]
        AgentBrain["Realtime Agent Brain"]
        ContextBuilder["Context Builder"]
        ToolRouter["Tool Router"]
    end

    subgraph Browser["Browser Runtime: Playwright"]
        BrowserSession["Isolated Browser Context"]
        ScreenReader["Screen Reader"]
        ActionExecutor["Safe Action Executor"]
        CursorEvents["Cursor Event Emitter"]
    end

    subgraph Learner["Learner Worker"]
        ProductLearner["Product Learner"]
        DemoGraph["Demo Graph Builder"]
        KnowledgeIndexer["Knowledge Indexer"]
    end

    subgraph Storage["Storage"]
        Postgres["Postgres + pgvector"]
        Redis["Redis Live State + Streams"]
        ObjectStore["MinIO/S3 Artifacts"]
    end

    subgraph Observability["Observability"]
        OTel["OpenTelemetry"]
        Prometheus["Prometheus"]
        Grafana["Grafana"]
        Loki["Loki"]
        Jaeger["Jaeger/Tempo"]
    end

    User --> Frontend
    Frontend --> API
    API --> Agent
    API --> Browser
    API --> Learner
    Agent --> Browser
    Agent --> Redis
    Browser --> Redis
    Browser --> ObjectStore
    Learner --> Postgres
    Learner --> Redis
    API --> Postgres
    API --> Redis
    Redis --> EventGateway
    EventGateway --> Frontend
    API --> Observability
    Agent --> Observability
    Browser --> Observability
    Learner --> Observability
```

## Core Boundaries

The system is deliberately split so fast realtime operations do not wait on slow learning, provider enrichment, or post-demo analysis.

| Service | Language/runtime | Responsibilities | Owns durable data? | Redis usage | Latency sensitivity | Scaling strategy | Security constraints |
| --- | --- | --- | --- | --- | --- | --- | --- |
| web | Next.js/React | Live UI, browser frame, cursor overlay, transcript panels | no | reads via API events | medium | HTTP/CPU | no backend secrets in `NEXT_PUBLIC_*` |
| api | FastAPI/Python | Products, sessions, orchestration, RBAC, event gateway | yes | locks, live state, streams | high for session APIs | HPA request/CPU | tenant-scoped queries and audit |
| agent-runtime | Python/Pipecat | Voice pipeline, context builder, agent brain, tool routing | transcript/action writes through APIs or repos | screen/actions/transcript window | very high | active calls/CPU | no raw browser authority |
| browser-runtime | TypeScript/Playwright | Browser contexts, screen read, safe actions, cursor events | artifact metadata through API/storage | browser status/events | high | active sessions/memory | sandbox, domain restrictions, no downloads |
| learner-worker | Python | Product graph, knowledge chunks, screen matching | yes | job state/events | low/cold path | queue depth | never blocks first audio |
| post-demo-worker | Python/API module | Insights, features shown, summary, mock CRM export | yes | job/events | low/cold path | queue depth | evidence and redaction required |
| tts-service | Python/service boundary | Optional local TTS | no | none or events | high if enabled | CPU/GPU | no provider keys in frontend |
| postgres | Postgres + pgvector | Durable system of record | yes | n/a | medium | managed DB preferred | tenant isolation |
| redis | Redis | Live state, streams, locks | ephemeral | n/a | high | managed Redis preferred | bounded keys/streams |
| minio | S3-compatible | Screenshots and artifacts | artifacts only | n/a | medium | object storage | no public raw secrets |
| observability | OTel/Prometheus/Loki/Grafana/Jaeger | Traces, metrics, logs, dashboards | telemetry | n/a | non-blocking | optional profile | no secrets in telemetry |

## End-to-End Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Web as Frontend
    participant API
    participant Agent
    participant Browser
    participant Redis
    participant DB as Postgres
    participant Learner

    User->>Web: enters URL
    Web->>API: create product/session
    API->>Browser: create session + navigate URL
    Browser->>Redis: current screen + safe actions
    API->>Agent: create voice session
    API->>Learner: enqueue product learning
    API-->>Web: join config + session state
    User->>Agent: speaks
    Agent->>Redis: read screen/actions/context
    Agent->>Agent: LLM structured decision
    Agent->>Browser: safe action command
    Browser->>Redis: cursor/action/screen events
    Redis-->>Web: live events
    API->>DB: persist transcript/actions/summary
```

## Session Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Prewarming: start_prewarm
    Prewarming --> WaitingForUser: prewarm_ready
    Prewarming --> DegradedReady: partial_prewarm_ready
    Prewarming --> Failed: prewarm_fatal_failure
    WaitingForUser --> Live: user_joined
    DegradedReady --> Live: user_joined
    Live --> Recovery: unexpected_browser_or_agent_state
    Recovery --> Live: recovered
    Recovery --> LiveDegraded: partially_recovered
    Recovery --> Ending: unrecoverable_or_user_ends
    Live --> Ending: user_ends_or_timeout
    LiveDegraded --> Ending: user_ends_or_timeout
    Ending --> Finalizing: resources_stopped
    Finalizing --> Completed: finalization_success
    Finalizing --> CompletedWithWarnings: nonfatal_finalization_failure
    Finalizing --> Failed: fatal_finalization_failure
```

Prewarming starts browser creation, URL load, first screen read, provider warmup, recipe compilation, voice session readiness, and learner enqueue before the user joins. Learner completion is never required before first audio.

## Agent Flow

```mermaid
flowchart TB
    Transcript["STT final transcript"] --> Context["Build compact context"]
    Context --> Prompt["Host agent prompt"]
    Prompt --> LLM["Provider-agnostic LLM"]
    LLM --> Validate["Validate strict JSON output"]
    Validate --> Speech["TTS response"]
    Validate --> Tool["Tool router"]
    Tool --> Policy["Policy and action ID check"]
    Policy --> Browser["Browser runtime command"]
    Browser --> Observe["Observe screen update"]
    Observe --> Memory["Memory update"]
```

Rules:

- The LLM does not get raw browser authority.
- The LLM chooses from bounded safe action IDs.
- Output validation rejects invalid structure and unsupported high-risk claims.
- The tool router sends browser commands only through the browser runtime.

## Browser Flow

```mermaid
flowchart TB
    Create["Create BrowserContext"] --> Navigate["Navigate allowed URL"]
    Navigate --> Read["Read current screen"]
    Read --> Extract["Extract visible text, DOM summary, accessibility, elements"]
    Extract --> Classify["Classify safe actions and risk"]
    Classify --> Redis["Publish current screen + safe actions"]
    Redis --> Command["Receive safe action command"]
    Command --> Validate["Validate action ID, visibility, policy"]
    Validate --> Cursor["Emit cursor move/highlight/click"]
    Cursor --> Playwright["Execute deterministic Playwright action"]
    Playwright --> Observe["Observe screen update"]
    Observe --> Redis
```

The cursor is synthetic and visual. Playwright performs deterministic actions. This gives the demo a human-like presentation without relying on the real OS cursor.

## Voice Flow

Pipecat is the voice/multimodal pipeline foundation. Pipecat describes itself as an open-source ecosystem for realtime voice and multimodal AI agents: [Pipecat introduction](https://docs.pipecat.ai/overview/introduction).

```mermaid
sequenceDiagram
    participant Browser as User Browser
    participant Agent as Agent Runtime
    participant STT
    participant Brain as Agent Brain
    participant TTS

    Browser->>Agent: audio/WebRTC or fake turn
    Agent->>Agent: VAD and turn detection
    Agent->>STT: speech to text
    STT-->>Agent: final transcript
    Agent->>Brain: process turn
    Brain-->>Agent: spoken response and optional action
    Agent->>TTS: synthesize response
    TTS-->>Browser: first audio/audio stream
```

## Memory and Context

```mermaid
flowchart TB
    T0["Tier 0: current screen in Redis"]
    T1["Tier 1: safe actions in Redis"]
    T2["Tier 2: recent transcript window"]
    T3["Tier 3: active recipe step"]
    T4["Tier 4: persona state"]
    T5["Tier 5: product summary"]
    T6["Tier 6: retrieved knowledge from pgvector"]
    T7["Tier 7: durable artifacts in Postgres/MinIO"]
    Builder["Context Builder"]

    T0 --> Builder
    T1 --> Builder
    T2 --> Builder
    T3 --> Builder
    T4 --> Builder
    T5 --> Builder
    T6 --> Builder
    T7 -.metadata only.-> Builder
```

Hot-path context is compact and bounded. Raw DOM, raw HTML, screenshots, audio, cookies, local storage, and provider responses are not placed in prompts.

## Safety Model

```mermaid
flowchart LR
    UserIntent["User intent"]
    LLMChoice["LLM safe action choice"]
    GlobalPolicy["Global hard blocks"]
    RecipePolicy["Recipe constraints"]
    RBAC["RBAC"]
    BrowserValidation["Browser runtime validation"]
    Audit["Audit log"]
    Execute{"Execute?"}

    UserIntent --> LLMChoice
    LLMChoice --> GlobalPolicy
    GlobalPolicy --> RecipePolicy
    RecipePolicy --> RBAC
    RBAC --> BrowserValidation
    BrowserValidation --> Audit
    Audit --> Execute
```

Recipe policy can make a demo stricter; it cannot override global hard blocks. Raw selectors, arbitrary JavaScript, destructive actions, billing/payment actions, and sensitive credential fields fail closed.

## Observability

```mermaid
flowchart TB
    Services["API / Agent / Browser / Learner / Post-Demo"]
    Traces["OpenTelemetry traces"]
    Metrics["Prometheus metrics"]
    Logs["Structured JSON logs"]
    Collector["OpenTelemetry Collector"]
    Prometheus["Prometheus"]
    Loki["Loki"]
    Jaeger["Jaeger/Tempo"]
    Grafana["Grafana dashboards"]

    Services --> Traces
    Services --> Metrics
    Services --> Logs
    Traces --> Collector
    Metrics --> Collector
    Logs --> Collector
    Collector --> Prometheus
    Collector --> Loki
    Collector --> Jaeger
    Prometheus --> Grafana
    Loki --> Grafana
    Jaeger --> Grafana
```

To debug slow first audio:

1. Open the realtime UX dashboard.
2. Find first-audio p95.
3. Open the trace for the session.
4. Compare STT, context build, LLM, TTS, and first audio spans.
5. Check `latency_budget.violation` logs.

## Hot Path vs Cold Path

| Path | Includes | Must not wait for |
| --- | --- | --- |
| Hot path | STT final, context build, LLM decision, TTS first audio, safe browser action | learner completion, post-demo summary, embeddings, CRM export |
| Cold path | learner jobs, graph updates, summaries, CRM dry-run export, eval artifacts | live user speech |

The engineering choice is deliberate: the user experience must feel fast and human, so slow enrichment work stays in the background.
