#!/usr/bin/env bash
set -euo pipefail

mode="${1:-default}"
detached="${COMPOSE_DETACHED:-false}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

python3 scripts/dev/ensure_ports.py

set -a
# shellcheck disable=SC1091
. .local/runtime/ports.env
set +a

services=(web api browser-runtime agent-runtime learner-worker post-demo-worker postgres redis minio)
profiles=()
stop_before_up=()

case "$mode" in
  default)
    stop_before_up=(ollama tts-service otel-collector prometheus grafana loki jaeger learner-worker-scrapegraph)
    ;;
  lite)
    export AI_TEXT_PROVIDER=fake AI_STT_PROVIDER=fake AI_TTS_PROVIDER=fake
    export LEARNER_ENABLED=false BROWSER_MAX_CONCURRENT_SESSIONS=1
    export NEXT_PUBLIC_PROVIDER_MODE_LABEL="Fake Providers"
    services=(web api browser-runtime agent-runtime postgres redis minio)
    stop_before_up=(
      learner-worker
      post-demo-worker
      ollama
      tts-service
      otel-collector
      prometheus
      grafana
      loki
      jaeger
      learner-worker-scrapegraph
    )
    ;;
  full)
    profiles=(--profile ai-local --profile tts-local --profile observability)
    services=()
    ;;
  observability)
    profiles=(--profile observability)
    services=()
    ;;
  ai-local)
    profiles=(--profile ai-local)
    services=()
    ;;
  nim)
    export AI_TEXT_PROVIDER=nvidia_nim
    stop_before_up=(ollama tts-service otel-collector prometheus grafana loki jaeger learner-worker-scrapegraph)
    ;;
  scrapegraph)
    export SCRAPEGRAPH_ENABLED=true SCRAPEGRAPH_TELEMETRY_ENABLED=false
    profiles=(--profile scrapegraph)
    services=(learner-worker-scrapegraph)
    ;;
  *)
    echo "Unknown up mode: $mode" >&2
    exit 2
    ;;
esac

if [ "${#stop_before_up[@]}" -gt 0 ]; then
  docker compose stop "${stop_before_up[@]}" >/dev/null 2>&1 || true
fi

echo
echo "Local URLs:"
echo "  Web:             ${WEB_URL}"
echo "  API:             ${API_URL}"
echo "  Browser runtime: ${BROWSER_RUNTIME_URL}"
echo "  Agent runtime:   ${AGENT_RUNTIME_URL}"
echo "  MinIO:           ${MINIO_URL}"
echo
echo "Opening after startup: make open"
echo "Health check:            make health"
echo

compose_args=(docker compose)
if [ "${#profiles[@]}" -gt 0 ]; then
  compose_args+=("${profiles[@]}")
fi
compose_args+=(up --build)
if [ "$detached" = "true" ]; then
  compose_args+=(-d)
fi
if [ "${#services[@]}" -gt 0 ]; then
  compose_args+=("${services[@]}")
fi

"${compose_args[@]}"
