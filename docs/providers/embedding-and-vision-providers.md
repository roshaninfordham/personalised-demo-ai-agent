# Embedding and Vision Providers

## Embeddings

Embeddings support fake, OpenAI-compatible, NVIDIA NIM, Ollama, and disabled modes.

Default local:

```env
AI_EMBEDDING_PROVIDER=fake
AI_EMBEDDING_DIMENSIONS=768
```

If switching dimensions:

1. Update configuration.
2. Add a database migration.
3. Reindex existing knowledge chunks.
4. Re-run retrieval tests.

## Vision

Vision is disabled by default:

```env
AI_VISION_PROVIDER=disabled
```

Vision should not run in the realtime hot path unless a future phase explicitly validates latency, redaction, prompt safety, and provider cost.
