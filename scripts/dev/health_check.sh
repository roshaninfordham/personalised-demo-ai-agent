#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"

python3 scripts/dev/ensure_ports.py
set -a
# shellcheck disable=SC1091
. .local/runtime/ports.env
set +a

check() {
  local name="$1"
  local url="$2"
  printf "%-18s" "$name"
  if curl -fsS --max-time 5 "$url" >/tmp/live-demo-health.json 2>/tmp/live-demo-health.err; then
    echo "healthy $url"
  else
    echo "unavailable $url"
    cat /tmp/live-demo-health.err || true
    return 1
  fi
}

failed=0
check "web" "${WEB_URL}" || failed=1
check "api" "${API_URL}/healthz" || failed=1
check "api-ready" "${API_URL}/readyz" || failed=1
check "browser-runtime" "${BROWSER_RUNTIME_URL}/healthz" || failed=1
check "agent-runtime" "${AGENT_RUNTIME_URL}/healthz" || failed=1
check "minio" "${MINIO_URL}/minio/health/live" || failed=1

if docker compose ps postgres redis >/dev/null 2>&1; then
  docker compose ps postgres redis
fi

exit "$failed"
