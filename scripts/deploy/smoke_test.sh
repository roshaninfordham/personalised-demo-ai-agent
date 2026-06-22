#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -f "${root}/.local/runtime/ports.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "${root}/.local/runtime/ports.env"
  set +a
fi

base_url="${SMOKE_BASE_URL:-${API_URL:-http://localhost:8000}}"
curl -fsS "${base_url}/healthz" >/dev/null
curl -fsS "${base_url}/readyz" >/dev/null || curl -fsS "${base_url}/healthz" >/dev/null
echo "Smoke test passed for ${base_url}."
