#!/usr/bin/env bash
set -euo pipefail

mode="${1:-default}"
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

case "$mode" in
  default)
    ;;
  lite)
    export AI_TEXT_PROVIDER=fake AI_STT_PROVIDER=fake AI_TTS_PROVIDER=fake
    services=(web api browser-runtime agent-runtime postgres redis minio)
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
if [ "${#services[@]}" -gt 0 ]; then
  compose_args+=("${services[@]}")
fi

"${compose_args[@]}"
