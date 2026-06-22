# Interview Demo Script

## Demo Goal

Show the core product loop: start the stack, enter a product URL, prewarm the session, let the agent read the screen, speak, move a cursor, click a safe element, answer a grounded question, adapt to the prospect, end the session, and produce an evidence-backed lead summary.

## Demo Setup

Safe fake/local mode:

```env
AI_TEXT_PROVIDER=fake
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
CRM_EXPORT_PROVIDER=mock
CRM_EXPORT_DRY_RUN=true
```

```bash
make up
```

More realistic NVIDIA NIM mode:

```env
AI_TEXT_PROVIDER=nvidia_nim
AI_TEXT_BASE_URL=https://integrate.api.nvidia.com/v1
AI_TEXT_API_KEY=<your-key>
AI_TEXT_MODEL=<model-name>
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
```

```bash
make up
```

Use fake STT/TTS if microphone or voice is unstable. Use scripted text turns if needed.

## Pre-Demo Checklist

- [ ] Docker is running.
- [ ] `.env` configured.
- [ ] No real secrets on screen.
- [ ] Health checks pass.
- [ ] Browser runtime ready.
- [ ] Agent runtime ready.
- [ ] Product URL available.
- [ ] Demo recipe or text guidance ready.
- [ ] Observability dashboard optional.
- [ ] Backup fake mode ready.

```bash
set -a
. .local/runtime/ports.env
set +a
curl -s $API_URL/healthz
curl -s $API_URL/readyz
curl -s $BROWSER_RUNTIME_URL/healthz
curl -s $AGENT_RUNTIME_URL/healthz
```

## Demo Flow

### Step 1: Start App

Say:

```text
I will start the full local stack. The key services are the frontend, API orchestrator, Pipecat agent runtime, Playwright browser runtime, Redis live state, Postgres, and MinIO artifacts.
```

Command:

```bash
make up
```

Open:

```bash
make open
```

Expected: landing page loads and the demo start form is visible.

### Step 2: Enter Product URL

Use:

```text
https://metric-master-suite505.apps.rebolt.ai/
```

Fallback local fixture if external site is unavailable:

```text
http://localhost:<fixture-port>
```

Optional guidance:

```text
This product helps founders track KPIs and understand business metrics.
Show the dashboard first, then metric creation, then reporting.
Avoid billing, delete, invite, payment, account settings, and publishing.
Target persona: founder.
```

Say:

```text
The agent can start from just a URL, but one-time guidance makes the demo more reliable. The production pattern is URL plus optional guidance or recipe.
```

### Step 3: Start Session and Prewarm

Expected events:

```text
session.prewarming.started
browser.session.created
browser.navigation.completed
browser.screen.updated
learner.started
session.readiness.updated
session.waiting_for_user
```

Say:

```text
Before the user joins, the orchestrator prewarms the browser, loads the URL, reads the first screen, prepares the voice session, compiles any recipe, and starts the learner in the background.
```

### Step 4: Agent Joins

Expected:

- join config created;
- agent runtime ready;
- call panel connected or fake mode ready.

Say:

```text
The voice runtime is Pipecat-based. For local reliability, this demo can use fake STT/TTS or real providers. The architecture is provider-swappable.
```

Pipecat docs describe the framework as an open-source ecosystem for realtime voice and multimodal AI agents: [Pipecat introduction](https://docs.pipecat.ai/overview/introduction).

### Step 5: Agent Learns Screen

Expected UI:

- browser viewport shows screenshot frame;
- learning sidebar shows loaded product URL;
- safe actions appear.

Say:

```text
The browser runtime reads DOM, accessibility hints, visible text, element bounding boxes, and screenshot metadata. It then creates safe action IDs. The LLM does not get raw browser authority.
```

### Step 6: Agent Explains

Example agent speech:

```text
From what I can verify on screen, this appears to be the main dashboard or overview area. I will start by explaining the visible metrics and navigation, then I can show the safest relevant workflow.
```

Say to interviewer:

```text
Notice the phrase "from what I can verify." The agent is explicitly grounded in observed evidence and avoids unsupported claims.
```

### Step 7: Cursor Moves and Clicks

Expected events:

```text
browser.action.started
browser.cursor.move
browser.element.highlight
browser.cursor.click
browser.action.completed
browser.screen.updated
```

Say:

```text
The cursor is synthetic and visual. Playwright performs deterministic actions. Separating the visual cursor from actual execution makes the demo feel human without sacrificing reliability.
```

### Step 8: User Asks Question

Ask:

```text
Can you show me how to create a new metric?
```

Expected:

- agent identifies Add Metric or Create Metric safe action;
- cursor moves;
- click happens;
- screen updates;
- agent explains result.

Then ask:

```text
Does this integrate with Salesforce?
```

Expected:

- agent does not claim Salesforce integration unless visible or in approved knowledge;
- agent says it cannot verify yet or offers to look.

Say:

```text
This demonstrates hallucination control. The agent can answer only from current screen, guidance, recipe, observed state, or retrieved knowledge.
```

### Step 9: Agent Adapts

Ask:

```text
I am a founder and I care mostly about weekly revenue reporting.
```

Expected:

- persona tracker updates founder/metrics/reporting interest;
- agent adapts talk track;
- lead insight persists after the session.

Say:

```text
The persona tracker is deterministic first and LLM-assisted later. It keeps the hot-path context compact while preserving useful sales intelligence.
```

### Step 10: End Session and Summarize Lead

Expected events:

```text
session.ending
session.ended
lead_summary.ready
crm_export.dry_run_completed
```

Expected summary:

- role: founder;
- interests: metrics, revenue reporting;
- features shown: dashboard, metric creation;
- questions: Salesforce integration;
- unanswered: Salesforce integration if not verified;
- recommended follow-up: reporting-focused follow-up.

Say:

```text
After shutdown, the system flushes transcript, closes the browser context, releases resources, extracts lead insights, generates an evidence-backed summary, and creates a mock CRM payload.
```

## What to Say

Keep the explanation anchored around four loops:

1. Voice loop: transport, VAD, turn detection, STT, agent response, TTS, interruption.
2. Browser loop: isolated context, screen read, safe action extraction, validated execution, observation.
3. Reasoning loop: compact context, provider-agnostic LLM, strict JSON validation, safe action IDs.
4. Learning loop: product summaries, demo graph, route suggestions, and knowledge chunks in the background.

## What to Click

Click only safe UI controls:

- demo start form;
- safe product navigation such as Dashboard, Reports, Add Metric;
- End Session.

Do not click billing, payment, delete, invite, account settings, publish, or external email controls in the demo.

## Expected Events

See [expected-demo-events.md](expected-demo-events.md).

## Expected Screens

- landing page;
- demo start form;
- live demo session;
- browser viewport with screenshot frame;
- cursor overlay;
- transcript panel;
- learning/readiness panel;
- session ended state;
- lead summary or post-demo job state.

## Fallback Script

If browser fails:

```text
The browser runtime failed to load the target URL, so I will switch to the local fixture app. The architecture is the same: controlled browser, screen reader, safe actions, cursor events, and grounded agent response.
```

If voice fails:

```text
The voice provider is optional in this local demo. I will switch to scripted text turns, which exercise the same agent brain, browser action router, safety policy, and post-demo summary.
```

If LLM provider fails:

```text
The provider abstraction lets us switch to fake or Ollama mode. I will use deterministic fake responses to show the browser and orchestration loop.
```

If hardware is slow:

```text
Local models are hardware-dependent, so I will keep LLM/STT/TTS in fake or hosted mode and focus on the core product loop.
```

## Technical Explanation for Interviewer

The system has four realtime loops.

First, the voice loop: Pipecat handles audio transport, VAD, turn detection, STT, agent response, TTS, and interruption.

Second, the browser loop: Playwright controls an isolated browser context, reads the screen, classifies safe actions, executes validated actions, and observes the result.

Third, the reasoning loop: the agent builds compact context from Redis and Postgres, calls a provider-agnostic LLM, validates strict JSON output, and routes only safe action IDs.

Fourth, the learning loop: a background learner builds product summaries, demo graph, route suggestions, and knowledge chunks without blocking the live demo.

The key safety principle is that the LLM never controls the browser directly. It can only select a safe action ID. The browser runtime and policy layer validate again before execution.

## Common Questions and Answers

**Why not let the LLM directly use Playwright?**

Because that is unsafe and nondeterministic. The LLM chooses intent or a safe action ID. The browser runtime validates visibility, risk, policy, and session state before executing deterministic Playwright actions.

**Why synthetic cursor?**

The real OS cursor is unreliable in headless/cloud browsers. A synthetic cursor gives the user a human-like demo while Playwright performs reliable actions.

**Why product graph?**

The graph gives the agent memory of screens and safe navigation paths. It lets the system recover when labels change and improves over repeated demos.

**Why optional guidance?**

URL-only mode is useful for exploration but not always reliable. Guidance or recipes turn it into a production-grade demo by providing goals, talk tracks, and forbidden actions.

**How do you prevent hallucination?**

The context builder includes source-attributed facts only. The agent prompt enforces grounded claims. The output validator rejects unsupported high-risk claims. If uncertain, the agent says what it can verify.

**How does it scale?**

API is stateless. Agent runtime scales by active voice sessions. Browser runtime scales by active browser sessions because it is memory-heavy. Learner and post-demo workers scale by queue depth. Redis and Postgres are shared infrastructure.

## After-Demo Summary

End by showing:

- session completed;
- resources released;
- transcript persisted;
- features shown;
- lead insights;
- lead summary;
- mock CRM export if enabled.
