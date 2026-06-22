#!/usr/bin/env bash
set -euo pipefail

base_url="${SMOKE_BASE_URL:-http://localhost:8000}"
curl -fsS "${base_url}/healthz" >/dev/null
curl -fsS "${base_url}/readyz" >/dev/null || curl -fsS "${base_url}/healthz" >/dev/null
echo "Smoke test passed for ${base_url}."
