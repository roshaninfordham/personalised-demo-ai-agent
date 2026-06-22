# Custom OpenAI-Compatible Provider

Use this mode for an endpoint that follows OpenAI-compatible chat completion semantics.

```env
AI_TEXT_PROVIDER=custom_openai_compatible
AI_TEXT_BASE_URL=https://your-provider.example.com/v1
AI_TEXT_API_KEY=<your-key>
AI_TEXT_MODEL=<model-name>
AI_TEXT_ENABLE_STREAMING=true
AI_TEXT_ENABLE_TOOL_CALLING=true
```

Requirements:

- compatible chat completion endpoint;
- timeout behavior that fits realtime budgets;
- tool calling support if browser action selection uses tools;
- strict JSON or structured output support, or reliable fallback validation;
- no prompt or provider response logging by default.

If the provider cannot satisfy structured output requirements, use fake mode for local tests or a validated hosted provider for demos.
