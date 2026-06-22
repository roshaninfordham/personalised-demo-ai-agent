# TTS Service

`services/tts_service` is the optional text-to-speech service boundary. The primary realtime voice pipeline lives in `services/agent_runtime`, but this package keeps TTS health and provider-facing service concerns isolated for local and future deployment modes.

## Boundary

```mermaid
flowchart LR
    Agent["Agent runtime"] --> TTS["TTS service boundary"]
    TTS --> Provider["TTS provider abstraction"]
    Provider --> Audio["Audio output / stream"]
```

## Health Role

```mermaid
sequenceDiagram
    participant API as Orchestrator/API
    participant Agent as Agent Runtime
    participant TTS as TTS Service

    API->>Agent: provider warmup / health
    Agent->>TTS: health check when configured
    TTS-->>Agent: ready/degraded
    Agent-->>API: readiness contribution
```

TTS warmup is bounded and should not block prewarm unless the deployment explicitly requires it.

## Verification

```bash
uv run pytest services/tts_service/tests
```

