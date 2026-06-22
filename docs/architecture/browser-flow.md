# Browser Flow

The browser runtime is the execution authority. It owns Playwright contexts, screen reads, safe action extraction, request blocking, cursor events, and cleanup.

```mermaid
sequenceDiagram
    participant API
    participant Runtime as Browser Runtime
    participant Page as Playwright Page
    participant Redis
    participant Store as MinIO/S3

    API->>Runtime: create session
    Runtime->>Page: new isolated BrowserContext
    Runtime->>Page: navigate allowed URL
    Runtime->>Page: read visible state
    Runtime->>Store: store screenshot artifact
    Runtime->>Redis: publish screen and safe actions
    API->>Runtime: execute safe action ID
    Runtime->>Redis: cursor move/highlight/click
    Runtime->>Page: deterministic Playwright action
    Runtime->>Page: observe screen update
    Runtime->>Redis: publish action completed and screen updated
```

Isolation rules:

- one BrowserContext per demo session;
- no shared cookies or storage;
- external navigation blocked unless configured;
- downloads and uploads blocked by default;
- context closed and temp files deleted on shutdown.
