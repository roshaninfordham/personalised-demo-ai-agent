# Ollama

Ollama is optional for local model experiments.

```env
AI_TEXT_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_TEXT_MODEL=<model-name>
```

```bash
docker compose --profile ai-local up --build
docker compose exec ollama ollama pull <model-name>
```

Ollama documents OpenAI API compatibility for parts of the API: [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility).

Local model behavior varies by model and hardware. Keep fake mode available for deterministic demos.
