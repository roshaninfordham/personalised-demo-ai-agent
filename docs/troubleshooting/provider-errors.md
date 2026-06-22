# Provider Errors

## Symptom

LLM calls fail, agent output is invalid, provider health is degraded, or the agent times out.

## Likely Causes

- 401/403 authentication failure.
- 429 rate limit.
- Timeout.
- Invalid model name.
- Tool calling unsupported by model/provider.
- JSON schema unsupported or unreliable.
- NVIDIA NIM base URL wrong.
- Ollama model not pulled.

## Quick Checks

```bash
grep AI_TEXT_ .env
docker compose logs api --tail=200
docker compose logs agent-runtime --tail=200
```

Ollama:

```bash
curl -s http://localhost:11434/api/version
docker compose exec ollama ollama list
```

## Logs and Metrics

Check:

- `llm.request.failed`;
- `provider_authentication_error`;
- `provider_rate_limited`;
- `invalid_agent_output`;
- LLM latency histogram;
- trace span `turn.llm_request`.

## Fix

- Verify `AI_TEXT_BASE_URL`.
- Verify `AI_TEXT_API_KEY`.
- Verify `AI_TEXT_MODEL`.
- Pull Ollama models manually.
- Switch to `AI_TEXT_PROVIDER=fake` for local debugging.
- Increase timeout only after confirming provider health.

## Prevention

Use fake providers in CI. Keep provider health checks visible before demos. Avoid unvalidated models for tool-calling flows.
