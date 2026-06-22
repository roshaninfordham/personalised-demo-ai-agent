# Data Flow

## Main Flow

```mermaid
sequenceDiagram
    participant Web
    participant API
    participant Browser
    participant Agent
    participant Redis
    participant DB as Postgres
    participant PostDemo

    Web->>API: create product
    Web->>API: create demo session
    API->>Browser: create browser session
    Browser->>Browser: navigate and read screen
    Browser->>Redis: current_screen and safe_actions
    API->>Agent: create voice session
    API-->>Web: readiness and join config
    Agent->>Redis: read compact live context
    Agent->>Browser: safe action command
    Browser->>Redis: cursor/action/screen events
    API->>DB: persist durable state
    API->>PostDemo: enqueue post-demo job after shutdown
```

## Durable vs Live State

| Store | State | Reason |
| --- | --- | --- |
| Postgres | organizations, products, sessions, transcripts, actions, recipes, summaries, audit logs | durable source of truth |
| Redis | current screen, safe actions, locks, streams, bounded transcript window | low-latency live state |
| MinIO/S3 | screenshots, traces, generated artifacts | large binary storage |

Live state is allowed to expire. Durable session status and audit history are not.
