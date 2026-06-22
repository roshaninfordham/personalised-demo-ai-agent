# Local Setup

## What You Will Run

The local stack runs the same service boundaries used by the production architecture, but with local infrastructure and fake providers by default.

| Service | Preferred host port | Purpose | Required for minimal demo? | Optional profile | Health endpoint |
| --- | ---: | --- | --- | --- | --- |
| web | 3000 | Frontend UI | yes | default | `/` |
| api | 8000 | Backend API and session orchestrator | yes | default | `/healthz` |
| browser-runtime | 8200 | Playwright browser control | yes | default | `/healthz` |
| agent-runtime | 8300 | Pipecat voice runtime and agent brain | yes for voice loop | default | `/healthz` |
| learner-worker | n/a | Product learner and demo graph worker | yes for full local flow | default | process health |
| postgres | 5432 | Durable DB and pgvector | yes | default | Compose healthcheck |
| redis | 6379 | Live state, locks, and streams | yes | default | Compose healthcheck |
| minio | 9000/9001 | S3-compatible artifacts | yes | default | `/minio/health/live` |
| ollama | 11434 | Local LLM/embedding runtime | optional | `ai-local` | `/api/version` |
| tts-service | 8100 | Optional local TTS service boundary | optional | `tts-local` | `/healthz` |
| otel/prometheus/loki/jaeger/grafana | 4317/9090/3100/16686/3001 | Local observability | optional | `observability` | service-specific |

These are preferred ports only. `make up` writes the actual assigned values to
`.local/runtime/ports.env` and automatically uses free alternatives when a
preferred port is already in use.

Docker Compose profiles selectively activate optional services. Docker documents profiles as a way to enable services for specific environments or use cases while keeping unprofiled services enabled by default: [Docker Compose profiles](https://docs.docker.com/compose/how-tos/profiles/).

## Prerequisites

- Docker and Docker Compose.
- Node `>=20`.
- pnpm `>=9`.
- Python `>=3.12`.
- `uv`.
- Git.
- Optional: NVIDIA NIM API key.
- Optional: Ollama for local models.
- Optional: GPU for local models.
- Optional: microphone and browser permissions for real voice input.

Verify your tools:

```bash
docker --version
docker compose version
node --version
pnpm --version
python --version
uv --version
```

## Quick Start: Fake Providers

This is the default path for local smoke tests and CI. It does not require paid APIs.

```bash
git clone <repo-url>
cd personalised-demo-ai-agent
cp .env.example .env
make up
```

Confirm the fake provider settings:

```bash
grep -E "AI_TEXT_PROVIDER|AI_STT_PROVIDER|AI_TTS_PROVIDER|CRM_EXPORT_PROVIDER|CRM_EXPORT_DRY_RUN" .env
```

Expected values for the free local path:

```text
AI_TEXT_PROVIDER=fake
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
TRANSPORT_PROVIDER=small_webrtc
CRM_EXPORT_PROVIDER=mock
CRM_EXPORT_DRY_RUN=true
```

Open the assigned local URL:

```bash
make open
```

`make up` detects free ports and writes the generated URLs to
`.local/runtime/ports.env`. To print them:

```bash
cat .local/runtime/ports.env
```

For any command in these docs that uses `$API_URL`, `$WEB_URL`,
`$BROWSER_RUNTIME_URL`, or similar generated variables, source the file first:

```bash
set -a
. .local/runtime/ports.env
set +a
```

## Run with Docker Compose

Default lightweight stack:

```bash
make up
```

Start in the background:

```bash
set -a
. .local/runtime/ports.env
set +a
make up
```

Follow logs:

```bash
docker compose logs -f api agent-runtime browser-runtime
```

Stop services:

```bash
docker compose down
```

## Optional Profiles

Services without profiles start by default. Profiled services start only when their profile is enabled.

```bash
# Include local Ollama.
make up-ai-local

# Include local TTS service.
make up-full

# Include observability stack.
make up-observability

# Include optional ScrapeGraphAI learner adapter.
make up-scrapegraph

# Include local AI, local TTS, and observability.
make up-full
```

## Run with NVIDIA NIM

Use NVIDIA NIM when you want hosted text inference behind the generic `AI_TEXT_*` abstraction.

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

NVIDIA documents NIM LLM as exposing an OpenAI-compatible API with chat completions, streaming, and tool calling: [NVIDIA NIM LLM API reference](https://docs.nvidia.com/nim/large-language-models/latest/api-reference.html).

Verification:

```bash
make up-nim
make health
```

More detail: [nvidia-nim-mode.md](nvidia-nim-mode.md).

## Run with Ollama

Use Ollama for no-cost local models when your hardware is strong enough.

```env
AI_TEXT_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_TEXT_MODEL=<already-pulled-model>

AI_EMBEDDING_PROVIDER=ollama
AI_EMBEDDING_BASE_URL=http://ollama:11434
AI_EMBEDDING_MODEL=nomic-embed-text
```

Start the profile:

```bash
make up-ai-local
```

Pull models manually:

```bash
docker compose exec ollama ollama pull <model-name>
docker compose exec ollama ollama pull nomic-embed-text
```

Ollama documents OpenAI API compatibility for connecting existing applications: [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility).

More detail: [ollama-mode.md](ollama-mode.md).

## Run with Local STT/TTS

Fake STT/TTS is the default deterministic path:

```env
AI_STT_PROVIDER=fake
AI_TTS_PROVIDER=fake
```

Local Whisper example:

```env
AI_STT_PROVIDER=whisper_cpp
WHISPER_CPP_BINARY_PATH=/path/to/whisper-cli
WHISPER_CPP_MODEL_PATH=/path/to/model.bin
```

Local TTS example:

```env
AI_TTS_PROVIDER=kokoro
KOKORO_BASE_URL=http://tts:8100
```

Start local TTS:

```bash
make up-full
```

Local STT/TTS latency depends on CPU/GPU, model size, and Docker resource limits. Use fake providers for deterministic CI and hosted providers for smoother demos if local hardware is weak.

More detail: [local-stt-tts.md](local-stt-tts.md).

## Verify Services

```bash
make health
```

Expected successful health responses are JSON health payloads with `status` equal to `ok` or HTTP 200 for service health endpoints.

Inspect Compose health:

```bash
docker compose ps
```

## Start a Demo Session

1. Run `make open`.
2. Enter a safe product URL.
3. Optional: paste text guidance from [demo-recipe-guide.md](../recipes/demo-recipe-guide.md).
4. Start the session.
5. Watch readiness, browser frame, transcript, and events.

For API-only smoke:

```bash
set -a
. .local/runtime/ports.env
set +a
curl -s "$API_URL/healthz"
```

## Shut Down

```bash
docker compose down
```

## Clean Reset

This deletes local Postgres, Redis, MinIO, Ollama, and Grafana volumes.

```bash
docker compose down -v
rm -rf .local/test-artifacts .local/mock-crm-exports
rm -f .local/runtime/ports.env
make up
```

Docker cleanup:

```bash
make clean-docker-safe
make clean-docker-deep
```

`clean-docker-deep` deletes unused images, containers, volumes, and build cache. It can free a lot of space but makes the next build slower. Use `clean-docker-safe` first.

## Common Local Issues

| Symptom | First check | Likely fix |
| --- | --- | --- |
| API not ready | `docker compose logs api --tail=200` | Run `make db-upgrade`, verify Postgres/Redis health |
| Browser runtime not ready | `docker compose logs browser-runtime --tail=200` | Increase Docker memory, verify MinIO health |
| NIM auth failure | `grep AI_TEXT_ .env` | Verify key, base URL, and model name |
| Ollama model missing | `docker compose exec ollama ollama list` | Pull the model manually |
| No microphone | browser site settings | Use localhost or HTTPS and grant mic permission |
| Slow first audio | Grafana realtime UX dashboard or logs | Use fake/cloud STT/TTS or reduce local model load |

## What This Local Setup Does Not Do

- It does not provision production secrets.
- It does not make real HubSpot or Salesforce writes.
- It does not prove production capacity.
- It does not require paid providers.
- It does not hide provider failures. Switch to fake mode to isolate local infrastructure from provider issues.
