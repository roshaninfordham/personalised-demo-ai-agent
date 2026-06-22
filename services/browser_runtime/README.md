# Browser Runtime Service

`services/browser_runtime` owns browser automation and is the final execution authority for browser commands. It exposes screen state, safe actions, cursor events, screenshots/artifacts metadata, and validated browser actions.

The service is TypeScript-based and uses Playwright internally.

## Execution Boundary

```mermaid
flowchart TB
    API["API orchestrator"]
    Agent["Agent runtime"]
    Learner["Learner worker"]
    Routes["Browser runtime routes"]
    Policy["Policy + action validator"]
    Playwright["Playwright context/page"]
    Extractor["Screen + element extractor"]
    Redis["Redis events/live state"]
    ObjectStore["MinIO/S3 artifacts"]

    API --> Routes
    Agent --> Routes
    Learner --> Routes
    Routes --> Policy
    Policy --> Playwright
    Playwright --> Extractor
    Extractor --> Redis
    Extractor --> ObjectStore
```

## Browser Command Safety

```mermaid
flowchart TD
    Command["Incoming command"] --> Shape["Validate command shape"]
    Shape --> Selector{"Raw selector or JS?"}
    Selector -->|yes| Block["Block"]
    Selector -->|no| ActionID["Resolve safe action / element"]
    ActionID --> Policy["Evaluate action policy"]
    Policy --> Decision{"Decision"}
    Decision -->|allowed| Execute["Execute Playwright action"]
    Decision -->|blocked| Block
    Decision -->|confirmation_required| Confirm["Return confirmation required"]
    Execute --> Observe["Read new screen"]
```

The browser runtime revalidates even when the API or agent already validated an action.

## Screen State Flow

```mermaid
sequenceDiagram
    participant Caller
    participant Runtime
    participant Page as Playwright Page
    participant Store as Redis/ObjectStore

    Caller->>Runtime: read_current_screen
    Runtime->>Page: extract visible elements/text
    Runtime->>Runtime: compute safe actions + hashes
    Runtime->>Store: publish safe metadata
    Runtime-->>Caller: screen_id, screen_hash, safe_actions
```

No raw screenshots/base64, cookies, localStorage, sessionStorage, or secrets should be placed into prompts or frontend-visible events.

## Verification

```bash
make browser-test
make browser-test-integration
pnpm --filter @live-demo-agent/browser-runtime test -- policy
```

