# Production Threat Model

```mermaid
flowchart TB
    Internet["User browser"] --> Web["Next.js web"]
    Web --> API["FastAPI API"]
    API --> Browser["Browser runtime"]
    API --> Agent["Agent runtime"]
    API --> Workers["Learner / post-demo workers"]
    Browser --> Product["Customer product URL"]
    API --> Data["Postgres / Redis / Object storage"]

    Product -. untrusted pages .-> Browser
    Browser -. safe events only .-> API
```

Primary risks:

- Browser runtime is exposed to arbitrary product pages.
- Provider and CRM credentials must never enter logs, metrics, images, or frontend payloads.
- Agent/browser actions must remain policy-gated even when recipes or LLM output are hostile.
- Worker queues must not create unbounded resource allocation.

Controls:

- Per-session Playwright contexts, blocked downloads/uploads, metadata endpoint blocking, and
  domain allowlists.
- Kubernetes non-root, restricted pods, read-only filesystems, explicit writable volumes, and
  no privilege escalation.
- Secrets injected through Kubernetes Secrets or future external secret managers.
- CI secret scans, image scans, manifest validation, lint/type/tests, and gated CD.
