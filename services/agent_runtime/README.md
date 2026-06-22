# Agent Runtime Service

`services/agent_runtime` owns the realtime voice loop and agent brain. It receives final transcripts, builds compact context, calls provider-agnostic LLM interfaces, validates structured decisions, streams TTS, routes safe browser actions, and records transcript/memory events.

## Runtime Boundary

```mermaid
flowchart TB
    Voice["Pipecat voice pipeline"]
    STT["STT provider"]
    Context["Realtime context builder"]
    Brain["Host agent brain"]
    Validator["Structured output validator"]
    TTS["TTS provider"]
    Tools["Tool router"]
    Memory["Memory handler"]
    Redis["Redis live state"]
    DB["Postgres"]
    Browser["Browser runtime"]

    Voice --> STT
    STT --> Context
    Context --> Redis
    Context --> DB
    Context --> Brain
    Brain --> Validator
    Validator --> TTS
    Validator --> Tools
    Validator --> Memory
    Tools --> Browser
    Memory --> DB
```

## Agent Decision Flow

```mermaid
sequenceDiagram
    participant STT
    participant Context
    participant LLM as TextGenerationProvider
    participant Validator
    participant TTS
    participant Router
    participant Browser

    STT->>Context: final user utterance
    Context-->>LLM: system prompt + bounded grounded context
    LLM-->>Validator: strict JSON decision
    Validator-->>TTS: spoken_response
    Validator-->>Router: optional browser_action action_id
    Router->>Browser: validated command
```

The agent runtime does not contain provider-specific business logic. It uses shared provider abstractions from `packages/backend_common`.

## Browser Authority Rule

```mermaid
flowchart LR
    LLM["LLM"] -->|action_id only| Validator["Validator"]
    Validator --> Router["Tool router"]
    Router --> Browser["Browser runtime"]
    Browser --> Policy["Browser-side validation"]
```

The LLM cannot output selectors, JavaScript, cookies, credentials, or unbounded browser commands.

## Context Sources

```mermaid
mindmap
  root((Realtime Context))
    Screen
      current screen summary
      safe action IDs
    Recipe
      active compiled step
      progress ratio
    Transcript
      bounded recent turns
    Persona
      role
      interests
      pain points
    Knowledge
      bounded retrieved facts
    Safety
      no raw selectors
      no unsupported claims
      no secrets
```

## Verification

```bash
make agent-test
make agent-brain-test
```
