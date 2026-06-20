# Personalised Demo AI Agent

Production-grade foundation for a live AI product-demo agent. The agent opens a product URL in an isolated browser, learns the interface, presents the product conversationally, controls the browser through safe validated actions, answers only from grounded evidence, and generates CRM-ready sales intelligence after the demo.

## Current Status

This repository currently contains the Phase 0 product and architecture foundation only. It intentionally does not implement the full application yet.

Phase 0 defines:

- Product requirements and live-demo behavior.
- Service architecture and boundaries.
- Provider-agnostic AI/browser/transport abstractions.
- Environment variable contract and `.env.example`.
- Security, determinism, latency, observability, and risk criteria.

## System At A Glance

```mermaid
flowchart TB
    User["User / Prospect"] --> Frontend["Frontend Web App"]
    Frontend --> API["API Backend"]
    Frontend <--> Transport["Realtime Transport"]

    API --> Agent["Pipecat Agent Runtime"]
    API --> Browser["Browser Runtime"]
    API --> Learner["Learner Worker"]

    Agent <--> Browser
    Browser --> Learner

    Agent --> Providers["Provider Adapters"]
    Browser --> Providers
    Learner --> Providers

    API --> Storage["PostgreSQL / Redis / Object Storage"]
    Agent --> Storage
    Browser --> Storage
    Learner --> Storage

    API --> Obs["Observability"]
    Agent --> Obs
    Browser --> Obs
    Learner --> Obs
```

## User And Agent Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as API Backend
    participant A as Agent Runtime
    participant B as Browser Runtime
    participant L as Learner Worker
    participant S as Storage

    U->>FE: Enter product URL and optional guidance
    FE->>API: Create demo session
    API->>B: Create isolated browser context
    API->>A: Start realtime agent session
    B->>B: Navigate and read first screen
    B->>L: Enqueue product learning
    A->>U: Greet and explain verified screen facts
    U->>A: Ask question or give direction
    A->>B: Request safe browser action by action ID
    B->>B: Validate risk and execute if allowed
    B->>FE: Emit cursor and screen events
    A->>U: Answer grounded in observed evidence
    A->>S: Store transcript events
    L->>S: Store graph, summaries, and lead insights
```

## Safety Model

The LLM is never given raw browser-control authority. It can choose only from precomputed safe actions, and the browser runtime validates every action before execution.

```mermaid
flowchart LR
    Intent["User intent / recipe step"] --> Candidates["Precomputed action candidates"]
    Candidates --> Risk["Risk scoring"]
    Risk --> Policy{"Policy decision"}
    Policy -- Low/Medium allowed --> Execute["Execute browser action"]
    Policy -- High risk --> Confirm["Ask explicit confirmation"]
    Policy -- Blocked --> Stop["Do not execute"]
    Execute --> Observe["Observe new screen state"]
    Observe --> Ground["Ground next response in evidence"]
```

## Provider-Agnostic Design

Provider choices are environment-driven. Business logic imports generic interfaces only.

```mermaid
flowchart TB
    Logic["Agents / Context Builders / Learners / API Routers"]
    Registry["Provider Registry"]
    Text["AI_TEXT_PROVIDER"]
    Vision["AI_VISION_PROVIDER"]
    Embed["AI_EMBEDDING_PROVIDER"]
    STT["AI_STT_PROVIDER"]
    TTS["AI_TTS_PROVIDER"]
    Browser["BROWSER_PROVIDER"]
    Transport["TRANSPORT_PROVIDER"]

    Logic --> Registry
    Registry --> Text
    Registry --> Vision
    Registry --> Embed
    Registry --> STT
    Registry --> TTS
    Registry --> Browser
    Registry --> Transport
```

NVIDIA NIM, OpenAI, Ollama, local models, and custom OpenAI-compatible providers fit behind the same generic provider contracts.

## Documentation Map

| File | Purpose |
| --- | --- |
| [architecture/README.md](architecture/README.md) | Architecture documentation index and visual navigation |
| [architecture/phase_0_product_requirements.md](architecture/phase_0_product_requirements.md) | Product behavior, modes, UX, safety, voice, cursor, learning, lead output |
| [architecture/phase_0_system_architecture.md](architecture/phase_0_system_architecture.md) | Services, boundaries, diagrams, hot/cold path, data structures, cybersecurity |
| [architecture/phase_0_provider_abstractions.md](architecture/phase_0_provider_abstractions.md) | Provider categories, interfaces, registry, errors, fallback, routing |
| [architecture/phase_0_environment_contract.md](architecture/phase_0_environment_contract.md) | Environment variables, local/cloud modes, secrets, service readers |
| [architecture/phase_0_acceptance_criteria.md](architecture/phase_0_acceptance_criteria.md) | Phase 0 completion checklist |
| [architecture/phase_0_risks_and_assumptions.md](architecture/phase_0_risks_and_assumptions.md) | Risks, assumptions, impact, mitigation phase |
| [.env.example](.env.example) | Complete provider-agnostic environment template |

## Repository Structure

```text
.
|-- README.md
|-- .env.example
`-- architecture
    |-- README.md
    |-- phase_0_product_requirements.md
    |-- phase_0_system_architecture.md
    |-- phase_0_provider_abstractions.md
    |-- phase_0_environment_contract.md
    |-- phase_0_acceptance_criteria.md
    `-- phase_0_risks_and_assumptions.md
```

## Phase 0 Acceptance Gate

```mermaid
flowchart TD
    A["Product behavior defined"] --> B["Service boundaries defined"]
    B --> C["Provider abstractions defined"]
    C --> D["Environment contract defined"]
    D --> E["Security and safety policies defined"]
    E --> F["Latency and observability targets defined"]
    F --> G["Risks and assumptions documented"]
    G --> H["Ready for implementation phases"]
```

## Implementation Notes

- Do not put provider SDKs in business logic.
- Do not let the LLM execute arbitrary JavaScript.
- Do not put full raw DOM into hot-path prompts.
- Do not make product claims without evidence.
- Do not expose provider secrets to the frontend.
- Keep the learner asynchronous so it never blocks live voice response.
