# Backend Common Package

`packages/backend_common` contains reusable Python implementation shared by backend services. It currently owns provider abstractions, provider adapters, policy engines, redaction helpers, and common tests.

## Dependency Role

```mermaid
flowchart TB
    Common["packages/backend_common"]
    Providers["AI provider interfaces + adapters"]
    Policy["Policy engines"]
    Redaction["Redaction helpers"]
    API["services/api"]
    Agent["services/agent_runtime"]
    Learner["services/learner_worker"]

    Common --> Providers
    Common --> Policy
    Common --> Redaction
    API --> Common
    Agent --> Common
    Learner --> Common
```

## Provider Abstraction

```mermaid
flowchart LR
    Service["Service code"] --> Interface["Text/Embedding/STT/TTS interfaces"]
    Interface --> Registry["Provider registry"]
    Registry --> Fake["Fake providers"]
    Registry --> OpenAICompatible["OpenAI-compatible"]
    Registry --> NIM["NVIDIA NIM"]
    Registry --> Ollama["Ollama/local"]
```

Business logic should depend on interfaces and provider purposes, not vendor SDKs.

## Policy Implementation

```mermaid
flowchart LR
    RuleJSON["packages/policies/rules"] --> Generated["generated policy constants"]
    Generated --> Engine["backend_common.policy"]
    Engine --> API["API"]
    Engine --> Agent["Agent runtime"]
    Engine --> Learner["Learner worker"]
```

Policy rule lists belong in `packages/policies`; this package implements deterministic evaluation.

## Verification

```bash
uv run pytest packages/backend_common/src/live_demo_backend_common/tests
```
