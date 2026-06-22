#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"

python3 scripts/dev/ensure_ports.py >/dev/null
set -a
# shellcheck disable=SC1091
. .local/runtime/ports.env
set +a

curl -s "${NEXT_PUBLIC_PROMETHEUS_URL}/-/healthy"
curl -s "${NEXT_PUBLIC_GRAFANA_URL}/api/health"
