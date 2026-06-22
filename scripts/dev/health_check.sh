#!/usr/bin/env bash
set -euo pipefail

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
check "web" "http://localhost:3000" || failed=1
check "api" "http://localhost:8000/healthz" || failed=1
check "api-ready" "http://localhost:8000/readyz" || failed=1
check "browser-runtime" "http://localhost:8200/healthz" || failed=1
check "agent-runtime" "http://localhost:8300/healthz" || failed=1
check "minio" "http://localhost:9000/minio/health/live" || failed=1

if docker compose ps postgres redis >/dev/null 2>&1; then
  docker compose ps postgres redis
fi

exit "$failed"
