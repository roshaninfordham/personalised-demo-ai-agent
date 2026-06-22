# Expected Demo Events

The event names below are safe frontend-visible event categories expected during a successful local demo.

```mermaid
sequenceDiagram
    participant API
    participant Browser
    participant Agent
    participant Redis
    participant Web

    API->>Redis: session.prewarming.started
    Browser->>Redis: browser.session.created
    Browser->>Redis: browser.screen.updated
    API->>Redis: session.readiness.updated
    API->>Redis: session.live.started
    Agent->>Redis: transcript.final
    Browser->>Redis: browser.action.started
    Browser->>Redis: browser.cursor.move
    Browser->>Redis: browser.element.highlight
    Browser->>Redis: browser.cursor.click
    Browser->>Redis: browser.action.completed
    Browser->>Redis: browser.screen.updated
    API->>Redis: session.ended
    API->>Redis: lead_summary.ready
    Redis-->>Web: event stream
```

Expected event list:

```text
session.prewarming.started
browser.session.created
browser.navigation.completed
browser.screen.updated
learner.started
session.readiness.updated
session.waiting_for_user
session.live.started
transcript.final
browser.action.started
browser.cursor.move
browser.element.highlight
browser.cursor.click
browser.action.completed
session.ending
session.ended
lead_summary.ready
crm_export.dry_run_completed
```
