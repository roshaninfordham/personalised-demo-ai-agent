# Local Free Mode

Local free mode is the recommended first run. It exercises orchestration, browser control, frontend events, safety policy, deterministic agent behavior, and post-demo mock CRM export without paid APIs.

```env
AI_TEXT_PROVIDER=fake
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
AI_EMBEDDING_PROVIDER=fake
AI_VISION_PROVIDER=disabled
CRM_EXPORT_PROVIDER=mock
CRM_EXPORT_DRY_RUN=true
```

Run:

```bash
cp .env.example .env
make up
```

What works in this mode:

- Product/session APIs.
- Browser prewarm and screen reading.
- Safe actions and cursor events.
- Session lifecycle and shutdown.
- Deterministic transcript/test paths.
- Evidence-backed post-demo summary path where fixture evidence exists.
- Mock CRM dry-run export.

What is intentionally simplified:

- Voice audio is fake or placeholder-driven.
- LLM responses are deterministic and not semantically rich.
- No paid provider is called.

Use this mode for CI, local smoke tests, and interviews where reliability matters more than natural voice quality.
