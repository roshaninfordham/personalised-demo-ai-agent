# Ollama Mode

Ollama is optional and useful for local no-cost experiments. It is not the default because model downloads, disk usage, and latency vary by machine.

Ollama documents OpenAI API compatibility for connecting existing applications: [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility).

## Environment

```env
AI_TEXT_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_TEXT_MODEL=<already-pulled-model>

AI_EMBEDDING_PROVIDER=ollama
AI_EMBEDDING_BASE_URL=http://ollama:11434
AI_EMBEDDING_MODEL=nomic-embed-text
AI_EMBEDDING_DIMENSIONS=768
```

## Run

```bash
docker compose --profile ai-local up --build
```

The project does not auto-pull models by default. Pull models manually so disk and network usage are explicit:

```bash
docker compose exec ollama ollama pull <model-name>
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama list
```

Verify:

```bash
curl -s http://localhost:11434/api/version
```

## Caveats

- OpenAI-compatible support can vary by Ollama version and model.
- Tool calling and structured JSON behavior are model-dependent.
- Local latency depends on CPU/GPU and model size.
- Embedding dimensions must match the database schema.

If debugging infrastructure, switch back to:

```env
AI_TEXT_PROVIDER=fake
AI_EMBEDDING_PROVIDER=fake
```
