# Architecture Documentation

This directory contains the Phase 0 foundation for the live AI demo-agent platform. The documents are intended to be implementable directly by a junior engineer and defensible in a staff-level architecture review.

## Phase 0 Package

```mermaid
flowchart TB
    Root["Phase 0 Foundation"]
    PRD["Product Requirements"]
    Arch["System Architecture"]
    Providers["Provider Abstractions"]
    Env["Environment Contract"]
    Example[".env.example"]
    Accept["Acceptance Criteria"]
    Risks["Risks and Assumptions"]

    Root --> PRD
    Root --> Arch
    Root --> Providers
    Root --> Env
    Env --> Example
    Root --> Accept
    Root --> Risks

    PRD --> Accept
    Arch --> Accept
    Providers --> Accept
    Env --> Accept
    Risks --> Accept
```

## Document Index

| Document                                                             | Main questions answered                                                                                     |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| [phase_0_product_requirements.md](phase_0_product_requirements.md)   | What does the product do, how does the live demo feel, and what must never happen?                          |
| [phase_0_system_architecture.md](phase_0_system_architecture.md)     | Which services exist, what does each own, and what is on the hot path?                                      |
| [phase_0_provider_abstractions.md](phase_0_provider_abstractions.md) | How can NVIDIA NIM, OpenAI, Ollama, local models, and future providers swap without business-logic changes? |
| [phase_0_environment_contract.md](phase_0_environment_contract.md)   | Which environment variables exist, who reads them, and which are secrets?                                   |
| [phase_0_acceptance_criteria.md](phase_0_acceptance_criteria.md)     | What must be true before Phase 0 is accepted?                                                               |
| [phase_0_risks_and_assumptions.md](phase_0_risks_and_assumptions.md) | What can fail, what is assumed, and when is each mitigation implemented?                                    |
| [phase_1_acceptance_checklist.md](phase_1_acceptance_checklist.md)   | What must be true before Phase 1 monorepo setup is accepted?                                                |

## Architecture Views

### Runtime View

```mermaid
flowchart LR
    FE["Frontend"]
    API["API Backend"]
    Agent["Agent Runtime"]
    Browser["Browser Runtime"]
    Learner["Learner Worker"]
    Storage["Storage"]
    Events["Event Bus"]
    Obs["Observability"]

    FE <--> API
    FE <--> Events
    API --> Agent
    API --> Browser
    API --> Learner
    Agent <--> Browser
    Browser --> Learner
    Agent <--> Events
    Browser <--> Events
    Learner <--> Events
    API --> Storage
    Agent --> Storage
    Browser --> Storage
    Learner --> Storage
    API --> Obs
    Agent --> Obs
    Browser --> Obs
    Learner --> Obs
```

### Hot Path View

```mermaid
flowchart LR
    A["User audio"] --> B["Turn detection"]
    B --> C["STT"]
    C --> D["Compact cached context"]
    D --> E["Streaming LLM first token"]
    E --> F["Streaming TTS first audio"]
    E --> G["Optional safe browser action"]
    G --> H["Cursor and screen update"]
```

Hot-path rule: do not require crawling, full DOM injection, embeddings, or vision on every voice turn.

### Cold Path View

```mermaid
flowchart LR
    URL["Product URL"] --> Crawl["Safe crawl / screen reads"]
    Crawl --> Summaries["Screen summaries"]
    Summaries --> Graph["Product demo graph"]
    Graph --> Index["Knowledge index"]
    Index --> Recipes["Recipe improvements"]
    Recipes --> NextDemo["Better future demos"]
```

Cold-path rule: background learning can improve future turns but must not block first audio or live voice response.

## Data And Evidence Flow

```mermaid
flowchart TB
    Screen["Observed screen state"]
    Transcript["Transcript events"]
    Action["Browser action results"]
    Evidence["Evidence references"]
    Lead["Lead insights"]
    CRM["CRM-ready payload"]

    Screen --> Evidence
    Transcript --> Evidence
    Action --> Evidence
    Evidence --> Lead
    Lead --> CRM
```

Every extracted sales insight must reference a `transcript_event_id`, `browser_action_id`, or `screen_id`.

## Safety Flow

```mermaid
stateDiagram-v2
    [*] --> CandidateAction
    CandidateAction --> ScoreRisk
    ScoreRisk --> Low: LOW
    ScoreRisk --> Medium: MEDIUM
    ScoreRisk --> High: HIGH
    ScoreRisk --> Blocked: BLOCKED

    Low --> Execute: visible and enabled
    Medium --> Execute: recipe allows or user clearly requests
    High --> Confirmation: ask explicit confirmation
    Confirmation --> Execute: user confirms
    Confirmation --> Stop: user declines
    Blocked --> Stop: never execute
    Execute --> ObserveNewState
    ObserveNewState --> [*]
    Stop --> [*]
```

## Provider Switching View

```mermaid
flowchart TB
    Env["Environment variables"]
    Registry["Provider registry"]
    Interfaces["Abstract interfaces"]
    Adapters["Provider adapters"]
    Services["Business services"]

    Env --> Registry
    Registry --> Adapters
    Adapters --> Interfaces
    Services --> Interfaces
```

Business services import interfaces only. Vendor-specific names belong inside adapters and environment variables.

## Recommended Reading Order

1. Start with [phase_0_product_requirements.md](phase_0_product_requirements.md).
2. Read [phase_0_system_architecture.md](phase_0_system_architecture.md) for service boundaries.
3. Read [phase_0_provider_abstractions.md](phase_0_provider_abstractions.md) before implementing any AI, browser, or transport integration.
4. Read [phase_0_environment_contract.md](phase_0_environment_contract.md) before adding configuration.
5. Use [phase_0_acceptance_criteria.md](phase_0_acceptance_criteria.md) as the implementation gate.
6. Review [phase_0_risks_and_assumptions.md](phase_0_risks_and_assumptions.md) before committing to Phase 1 scope.
