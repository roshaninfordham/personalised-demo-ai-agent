# User And Agent Flows

This document explains how a user moves through a demo and how the agent coordinates speech, screen state, browser actions, recipes, safety, and recovery.

## User Journey

```mermaid
journey
    title Live Product Demo Journey
    section Setup
      Create product URL: 3: User, API
      Create demo session: 3: User, API
      Prewarm browser and voice: 4: Orchestrator
    section Join
      Frontend receives readiness: 4: Web
      User joins call: 5: User
      Agent greets honestly: 5: Agent
    section Demo
      User asks question: 5: User
      Agent answers from grounded context: 5: Agent
      Agent routes safe browser action: 4: Agent, Browser
      Frontend shows cursor and screen update: 5: Web
    section Recovery
      Unexpected state detected: 2: Browser, Orchestrator
      Agent rechecks screen safely: 4: Agent
      User clarifies if needed: 4: User
    section End
      Session ends: 4: User, API
      Resources are cleaned: 5: Orchestrator
      Summary is queued or created: 4: API
```

## Demo Creation To Prewarm

```mermaid
sequenceDiagram
    participant User
    participant Web
    participant API
    participant Orch as Orchestrator
    participant Browser
    participant Agent
    participant Learner
    participant Redis
    participant DB as Postgres

    User->>Web: enters product URL
    Web->>API: create product
    API->>DB: persist product
    Web->>API: create demo session
    API->>DB: persist session
    Web->>API: prewarm session
    API->>Orch: prewarm_session
    par Browser prewarm
        Orch->>Browser: create session + navigate + read screen
        Browser->>Redis: publish screen + safe actions
    and Voice prewarm
        Orch->>Agent: create voice session
    and Learner cold path
        Orch->>Learner: enqueue learning job
    and Recipe/Provider warmup
        Orch->>API: compile recipe if present
    end
    Orch->>Redis: readiness state
    Orch->>DB: resource allocations + run status
    API-->>Web: readiness + join config
```

## Live Agent Turn

```mermaid
sequenceDiagram
    participant User
    participant Voice as Agent Runtime
    participant Context
    participant LLM
    participant Validator
    participant Sync as Browser-Agent Sync
    participant TTS
    participant Browser
    participant Web

    User->>Voice: speaks
    Voice->>Voice: VAD + STT final
    Voice->>Context: user utterance + session_id
    Context-->>Voice: compact grounded context
    Voice->>LLM: deterministic structured request
    LLM-->>Validator: JSON decision
    Validator-->>Voice: spoken response + optional action_id
    Voice->>TTS: start speech
    Voice->>Sync: action selected
    Sync->>Browser: queue action after speech starts
    Browser-->>Web: cursor move
    Browser-->>Web: element highlight
    Browser-->>Web: click
    Browser-->>Web: screen updated
```

## Browser Action UX Order

```mermaid
flowchart TD
    Decision["Validated agent decision"] --> Speech{"spoken_response?"}
    Speech -->|yes| StartTTS["Start TTS immediately"]
    Speech -->|no| ActionType{"Low-risk read/highlight?"}
    StartTTS --> WaitStart["Wait for speech_started or bounded delay"]
    WaitStart --> Queue["Queue browser action"]
    ActionType -->|yes| Queue
    ActionType -->|no| Reject["Reject empty-speech risky action"]
    Queue --> Cursor["Cursor move"]
    Cursor --> Highlight["Highlight element"]
    Highlight --> Click["Click or execute safe command"]
    Click --> Observe["Wait for screen update"]
    Observe --> Done["Continue next turn"]
```

This gives the user a presenter-like rhythm: the agent begins speaking, then moves and clicks.

## Recipe-Guided Demo Loop

```mermaid
flowchart LR
    Progress["Recipe progress state"] --> Active["Active compiled step"]
    Active --> Match["Match step to current screen/actions"]
    Match --> Context["Agent context includes active step"]
    Context --> Decision["LLM chooses speech + safe action_id"]
    Decision --> Router["Tool router validates action_id"]
    Router --> Browser["Browser runtime executes"]
    Browser --> Result["Action/screen result"]
    Result --> Complete["Progress tracker evaluates completion"]
    Complete --> Progress
```

The hot path reads compiled recipe payloads, not raw large recipe JSON.

## Recovery Flow

```mermaid
flowchart TD
    Trigger["Recovery trigger"] --> Pause["Pause new browser actions"]
    Pause --> Read["read_current_screen"]
    Read --> Safe{"Screen safe and available?"}
    Safe -->|yes| Refresh["Refresh Redis current_screen + safe_actions"]
    Refresh --> Live["Return to live"]
    Safe -->|no| Back{"go_back allowed?"}
    Back -->|yes| GoBack["Try safe go_back"]
    GoBack --> Read
    Back -->|no| Home{"navigate home allowed?"}
    Home -->|yes| NavigateHome["Navigate start_url"]
    NavigateHome --> Read
    Home -->|no| Ask["Ask user / explain uncertainty"]
    Ask --> Attempts{"Attempts exceeded?"}
    Attempts -->|no| LiveDegraded["Live degraded"]
    Attempts -->|yes| Ending["Ending"]
```

Recovery actions are limited to safe screen read, highlight, go back, and home navigation.

## Shutdown Flow

```mermaid
sequenceDiagram
    participant API
    participant Orch as Orchestrator
    participant Agent
    participant Browser
    participant Learner
    participant Redis
    participant DB as Postgres

    API->>Orch: shutdown_session
    Orch->>DB: status=ending
    Orch->>Redis: stop accepting actions
    par Cleanup
        Orch->>Agent: stop voice + flush transcript
        Orch->>Browser: close browser session
        Orch->>Learner: detach/cancel learner run
    end
    Orch->>DB: deterministic summary / summary queued
    Orch->>Redis: release pending state, retain final compact state
    Orch->>DB: mark resources released
    Orch->>DB: status=completed or completed_with_warnings
```

Duplicate shutdown calls return the existing completed or ending state instead of repeating side effects.

## Safety Decision Flow

```mermaid
flowchart TD
    LLM["LLM proposes browser_action.action_id"] --> Validator["Output validator"]
    Validator --> Router["Tool router"]
    Router --> Policy["Policy engine"]
    Policy --> Decision{"Policy decision"}
    Decision -->|allowed| Browser["Browser runtime validates again"]
    Decision -->|confirmation_required| Ask["Ask for human confirmation"]
    Decision -->|blocked| Fallback["Speak safe fallback"]
    Browser --> Event["Persist audit/event"]
```

The LLM never chooses selectors, JavaScript, credentials, or unvalidated browser commands.
