# Troubleshooting

Use this format for every issue:

## Symptom

What the user or engineer sees.

## Likely Causes

The most common causes in local development.

## Quick Checks

Commands to run first.

## Logs and Metrics

Where to inspect evidence.

## Fix

Specific remediation steps.

## Prevention

How to reduce recurrence.

## Common Categories

| Category | Guide |
| --- | --- |
| Browser failures | [browser-failures.md](browser-failures.md) |
| Microphone and WebRTC | [microphone-and-webrtc.md](microphone-and-webrtc.md) |
| Provider errors | [provider-errors.md](provider-errors.md) |
| TTS/STT failures | [tts-stt-failures.md](tts-stt-failures.md) |
| Slow local hardware | [slow-local-hardware.md](slow-local-hardware.md) |
| Docker Compose | [docker-compose.md](docker-compose.md) |
| Database, Redis, MinIO | [database-redis-minio.md](database-redis-minio.md) |
| Observability | [observability.md](observability.md) |
| Error codes | [common-error-codes.md](common-error-codes.md) |

## First Commands

```bash
set -a
. .local/runtime/ports.env
set +a
docker compose ps
curl -s $API_URL/healthz
curl -s $API_URL/readyz
curl -s $BROWSER_RUNTIME_URL/healthz
curl -s $AGENT_RUNTIME_URL/healthz
docker compose logs api --tail=100
docker compose logs browser-runtime --tail=100
docker compose logs agent-runtime --tail=100
```
