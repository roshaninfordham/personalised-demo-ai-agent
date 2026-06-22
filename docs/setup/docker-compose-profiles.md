# Docker Compose Profiles

The default Compose stack starts services required for the local demo: `web`, `api`, `agent-runtime`, `browser-runtime`, `learner-worker`, `postgres`, `redis`, and `minio`.

Optional services use Compose profiles:

| Profile | Starts | Use when |
| --- | --- | --- |
| `ai-local` | `ollama` | You want local LLM or embedding models |
| `tts-local` | `tts-service` | You want to test the local TTS service boundary |
| `observability` | OTel Collector, Prometheus, Grafana, Loki, Jaeger | You want traces, metrics, logs, and dashboards |

Docker Compose profiles let a single Compose file selectively activate services for different use cases: [Docker Compose profiles](https://docs.docker.com/compose/how-tos/profiles/).

```bash
docker compose up --build
docker compose --profile ai-local up --build
docker compose --profile tts-local up --build
docker compose --profile observability up --build
docker compose --profile ai-local --profile tts-local --profile observability up --build
```

Expected behavior:

- Unprofiled services always start.
- Profiled services start only when the profile is active.
- Local fake-provider mode does not require any optional profile.

Troubleshooting:

```bash
docker compose config
docker compose ps
docker compose logs --tail=200
```
