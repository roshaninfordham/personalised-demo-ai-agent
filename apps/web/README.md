# Web App

`apps/web` is the Next.js frontend for starting and observing live demo sessions. It renders readiness, browser screen state, cursor/action events, transcript panels, learning/sidebar events, recipe progress, and session lifecycle state.

## Frontend Architecture

```mermaid
flowchart TB
    User["User"]
    App["Next.js App Router"]
    APIClient["API client"]
    Events["Event client"]
    Reducer["Event reducer"]
    Stores["Bounded client stores"]
    UI["Demo UI panels"]
    API["services/api"]

    User --> App
    App --> APIClient
    App --> Events
    APIClient --> API
    Events --> API
    Events --> Reducer
    Reducer --> Stores
    Stores --> UI
```

## Session UI Flow

```mermaid
stateDiagram-v2
    [*] --> Setup
    Setup --> Prewarming: product/session created
    Prewarming --> WaitingForUser: readiness ready
    Prewarming --> DegradedReady: partial readiness
    WaitingForUser --> Live: join/start
    DegradedReady --> Live: join/start
    Live --> Recovery: recovery event
    Recovery --> Live: resolved
    Recovery --> LiveDegraded: partial recovery
    Live --> Ending: user ends
    LiveDegraded --> Ending: user ends
    Ending --> Completed: ended event
```

## Event Reducer Inputs

```mermaid
flowchart LR
    Streams["API event stream"] --> Reducer["eventReducer"]
    Reducer --> Session["session state"]
    Reducer --> Browser["browser frame state"]
    Reducer --> Transcript["transcript state"]
    Reducer --> Learning["learning/sidebar state"]
    Reducer --> Recovery["recovery state"]
```

The reducer consumes frontend-safe, typed orchestration and runtime events. It should not receive provider secrets, raw prompts, raw screenshots/base64, cookies, tokens, or internal service credentials.

## API Client Surface

```mermaid
flowchart TD
    DemoForm["DemoStartForm"] --> CreateProduct["create product"]
    CreateProduct --> CreateSession["create session"]
    CreateSession --> Prewarm["prewarm session"]
    Prewarm --> Join["get join config / start"]
    Join --> State["orchestration state"]
    State --> End["end session"]
```

## Verification

```bash
pnpm --filter @live-demo-agent/web lint
pnpm --filter @live-demo-agent/web typecheck
pnpm --filter @live-demo-agent/web test
```
