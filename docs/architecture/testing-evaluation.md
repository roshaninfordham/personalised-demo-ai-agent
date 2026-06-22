# Testing and Evaluation

Phase 15 adds the deterministic quality system for safety, browser control, session
orchestration, agent grounding, latency regression detection, and local capacity checks.

It is intentionally layered. Fast tests run on every PR, while full E2E and load scenarios
are available for main branch, release, and manual validation.

## Quality Pyramid

```mermaid
flowchart TB
    Unit["Unit<br/>policy, ranker, context"]
    Contract["Contract<br/>schemas and generated DTOs"]
    Integration["Integration<br/>browser, storage, lifecycle"]
    E2E["E2E<br/>web, API, agent, browser"]
    Evals["Agent Evals<br/>grounding, safety, recovery"]
    Load["Load<br/>k6, Locust, leak checks"]

    Unit --> Contract
    Contract --> Integration
    Integration --> E2E
    E2E --> Evals
    Evals --> Load
```

## Default Provider Mode

```mermaid
flowchart LR
    Tests["Quality gates"] --> FakeAI["Fake LLM/STT/TTS"]
    Tests --> FixtureApps["Local fixture apps"]
    Tests --> MockCRM["Mock CRM"]
    Tests --> LocalInfra["Postgres / Redis / MinIO"]
    FakeAI --> Determinism["Deterministic results"]
    FixtureApps --> Safety["No external destructive actions"]
```

The default path does not require NVIDIA NIM, Daily, Deepgram, Cartesia, HubSpot,
Salesforce, or any paid observability or CRM vendor.

## Browser Fixture Apps

```mermaid
flowchart TB
    Apps["tests/fixtures/browser_apps"]
    Apps --> Simple["simple-dashboard<br/>dashboard, metrics, reports"]
    Apps --> Risky["risky-actions-app<br/>delete, billing, invite, publish"]
    Apps --> Dynamic["dynamic-spa<br/>delayed render, modal, stale element"]

    Simple --> SafeClicks["safe click and extraction tests"]
    Risky --> PolicyBlocks["blocked/high-risk policy tests"]
    Dynamic --> Recovery["self-healing and recovery tests"]
```

## Session Lifecycle Test

```mermaid
sequenceDiagram
    participant Test
    participant API
    participant Browser
    participant Agent
    participant Redis
    participant DB

    Test->>API: create product/session
    Test->>API: prewarm
    API->>Browser: create session + read first screen
    API->>Redis: current screen + safe actions
    Test->>API: start
    API->>Agent: create/reuse voice session
    Test->>DB: seed transcript/action evidence
    Test->>API: end
    API->>Agent: stop/flush transcript
    API->>Browser: close context
    API->>DB: completed + released resources
```

## Agent Quality Evals

```mermaid
flowchart LR
    Dataset["JSONL eval dataset"] --> Runner["run_agent_quality_evals.py"]
    Runner --> Grounding["Grounding scorer"]
    Runner --> Hallucination["Hallucination scorer"]
    Runner --> Recipe["Recipe completion scorer"]
    Runner --> Recovery["Recovery scorer"]
    Runner --> Safety["Safety scorer"]
    Runner --> Report["eval_report.json/xml"]
```

Eval gates:

- `safety_violations = 0`
- `hallucination_count = 0` for critical unsupported capability cases
- `grounding_score_avg >= 0.95`
- `recipe_completion_score_avg >= 0.80`
- `recovery_success_rate >= 0.90`

## Load and Leak Checks

```mermaid
flowchart TB
    K6["k6 HTTP thresholds"] --> Summary["k6-summary.json"]
    Locust["Locust session behavior"] --> Stats["locust-stats.csv"]
    Cleanup["Resource leak check"] --> LeakReport["resource-leak-report.json"]

    Summary --> Reports[".local/load-results"]
    Stats --> Reports
    LeakReport --> Reports
```

Local targets are deliberately conservative:

- 1 concurrent full demo succeeds.
- 5 lightweight sessions complete with API error rate below 1%.
- Browser worker limits return controlled `429` or queued state.
- Completed sessions leave no active browser sessions, voice sessions, stale locks, or active resource allocations.

## CI Matrix

```mermaid
flowchart TB
    PR["Pull request"] --> Unit["test-fixture-secrets"]
    PR --> PyUnit["test-unit"]
    PR --> Contracts["contracts"]
    PR --> LintType["lint + typecheck"]

    Main["Main branch"] --> Browser["test-browser"]
    Main --> Lifecycle["test-session-lifecycle"]
    Main --> E2E["test-e2e"]
    Main --> Evals["test-evals"]
    Main --> LoadSmoke["test-load-smoke"]

    Manual["Manual / release"] --> LoadLocal["test-load-local"]
```

The workflow in `.github/workflows/test.yml` keeps slow/load gates separate from the
core PR feedback path.

## Reports

Machine-readable outputs are generated at:

- `.local/test-results/unit-results.xml`
- `.local/test-results/integration-results.xml`
- `.local/test-results/e2e-results.xml`
- `tests/evals/reports/eval_report.json`
- `tests/evals/reports/eval_report.xml`
- `.local/load-results/k6-summary.json`
- `.local/load-results/locust-stats.csv`
- `.local/load-results/resource-leak-report.json`
- `.local/test-results/artifact-index.json`

## Limitations

Phase 15 validates deterministic local quality gates. It does not claim production load
capacity, live-provider quality, or real CRM integration correctness. Those remain opt-in
release gates with explicit credentials and environment controls.
