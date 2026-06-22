# LLM Providers

Text generation providers are configured through `AI_TEXT_*` variables.

Supported local configuration values:

- `fake`
- `nvidia_nim`
- `openai`
- `custom_openai_compatible`
- `ollama`
- `disabled`

Use [provider-switching.md](provider-switching.md) for the full switching guide.

Important rules:

- Business logic uses `TextGenerationProvider`.
- Provider adapters may call external services.
- Tool calls returned by the model are data; the provider layer does not execute tools.
- Prompt text and provider responses are not logged by default.
- Realtime host temperature should stay deterministic unless intentionally changed.
