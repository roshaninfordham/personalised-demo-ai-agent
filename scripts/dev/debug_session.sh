#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"

session_id="${1:-${session:-}}"
if [ -z "$session_id" ]; then
  echo "Usage: make debug-session session=<demo_session_id>" >&2
  exit 2
fi

python3 scripts/dev/ensure_ports.py >/dev/null
set -a
# shellcheck disable=SC1091
. .local/runtime/ports.env
set +a

prefix="${REDIS_KEY_PREFIX:-live_demo}"
stream_key="${prefix}:stream:session:${session_id}:events"

section() {
  printf "\n== %s ==\n" "$1"
}

pretty_curl() {
  local url="$1"
  curl -fsS "$url" | python3 -m json.tool || true
}

section "Session"
pretty_curl "${API_URL}/api/v1/demo-sessions/${session_id}"

section "Session state"
pretty_curl "${API_URL}/api/v1/demo-sessions/${session_id}/state"

section "Orchestration state"
pretty_curl "${API_URL}/api/v1/demo-sessions/${session_id}/orchestration-state"

section "Redis current screen"
docker compose exec -T redis redis-cli GET "${prefix}:session:${session_id}:current_screen" | python3 -m json.tool || true

section "Redis safe actions"
docker compose exec -T redis redis-cli GET "${prefix}:session:${session_id}:safe_actions" | python3 -m json.tool || true

section "Redis browser status"
docker compose exec -T redis redis-cli GET "${prefix}:session:${session_id}:browser_status" | python3 -m json.tool || true

section "Last 20 session stream events"
docker compose exec -T redis redis-cli XREVRANGE "$stream_key" + - COUNT 20 || true

section "Artifact URL candidates"
state_json="$(curl -fsS "${API_URL}/api/v1/demo-sessions/${session_id}/state" || true)"
STATE_JSON="$state_json" python3 - "$API_URL" <<'PY'
import json
import os
import sys
from urllib.parse import quote

api_url = sys.argv[1].rstrip("/")
raw = os.environ.get("STATE_JSON", "")
try:
    state = json.loads(raw)
except json.JSONDecodeError:
    raise SystemExit(0)
screen = (((state.get("live_state") or {}).get("current_screen")) or {})
for key in ("image_url", "screenshot_url"):
    if screen.get(key):
        print(f"{key}: {screen[key]}")
uri = screen.get("screenshot_uri")
if uri:
    print(f"screenshot_uri: {uri}")
    print(f"api_proxy: {api_url}/api/v1/artifacts/browser-screenshot?object_key={quote(uri, safe='')}")
PY

section "API logs containing session"
docker compose logs --tail=500 api 2>/dev/null | grep -F "$session_id" -C 3 || true

section "Browser runtime logs containing session"
docker compose logs --tail=500 browser-runtime 2>/dev/null | grep -F "$session_id" -C 3 || true
