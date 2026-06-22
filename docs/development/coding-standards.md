# Coding Standards

## Boundaries

- Use generated contracts where available.
- Keep provider-specific code inside adapters.
- Keep browser execution inside browser runtime.
- Keep policy and redaction shared where possible.
- Do not put backend secrets in frontend code.

## Safety

- Fail closed on unsafe browser actions.
- Validate LLM output before using it.
- Redact before prompts, logs, summaries, and CRM payloads.
- Audit high-impact actions.

## Performance

- Use bounded buffers.
- Use monotonic clocks for durations.
- Keep learner and post-demo work off the live hot path.
- Do not add unbounded queues or retries.

## Documentation

- Prefer Markdown docs with Mermaid diagrams.
- Mark optional and unimplemented behavior honestly.
- Use placeholder keys only.
