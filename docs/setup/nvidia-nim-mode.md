# NVIDIA NIM Mode

NVIDIA NIM is optional. The codebase uses it through generic `AI_TEXT_*` provider settings, so business logic does not import NVIDIA-specific code.

NVIDIA documents NIM LLM as exposing an OpenAI-compatible inference API with chat completions, streaming, and tool calling: [NVIDIA NIM LLM API reference](https://docs.nvidia.com/nim/large-language-models/latest/api-reference.html).

## Environment

```env
AI_TEXT_PROVIDER=nvidia_nim
AI_TEXT_BASE_URL=https://integrate.api.nvidia.com/v1
AI_TEXT_API_KEY=<your-key>
AI_TEXT_MODEL=<model-name>
AI_TEXT_ENABLE_STREAMING=true
AI_TEXT_ENABLE_TOOL_CALLING=true
AI_TEXT_TEMPERATURE=0.0
AI_TEXT_TOP_P=1.0
```

Optional embeddings:

```env
AI_EMBEDDING_PROVIDER=nvidia_nim
AI_EMBEDDING_BASE_URL=https://integrate.api.nvidia.com/v1
AI_EMBEDDING_API_KEY=<your-key>
AI_EMBEDDING_MODEL=<embedding-model>
AI_EMBEDDING_DIMENSIONS=768
```

Embedding dimensions must match the pgvector schema. Changing dimensions requires migration and reindexing.

## Run

```bash
make up api agent-runtime learner-worker
curl -s $API_URL/readyz
```

If a provider health endpoint is enabled:

```bash
curl -s $API_URL/api/v1/provider-health
```

## Common Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Authentication error | Missing or invalid key | Verify `AI_TEXT_API_KEY` |
| Model not found | Wrong model name | Check the model name in NVIDIA docs/account |
| Tool output invalid | Model/provider mode lacks required structured behavior | Switch to fake mode or a model known to support tools |
| Slow response | Provider latency or rate limit | Check traces and provider status |

No real keys are shown in this document.
