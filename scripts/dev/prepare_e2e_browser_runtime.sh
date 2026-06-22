#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root"

python3 scripts/dev/ensure_ports.py >/dev/null
set -a
# shellcheck disable=SC1091
. .local/runtime/ports.env
set +a

ready_json="$(curl -fsS --max-time 5 "${BROWSER_RUNTIME_URL}/readyz" 2>/dev/null || true)"

if [ -z "$ready_json" ]; then
  echo "browser-runtime is not reachable at ${BROWSER_RUNTIME_URL}."
  echo "Start the local stack first with: make up"
  exit 1
fi

active_sessions="$(READY_JSON="$ready_json" python3 - <<'PY'
import json
import os

try:
    payload = json.loads(os.environ["READY_JSON"])
except Exception:
    print("unknown")
    raise SystemExit(0)
print(payload.get("active_sessions", 0))
PY
)"

capacity="$(READY_JSON="$ready_json" python3 - <<'PY'
import json
import os

try:
    payload = json.loads(os.environ["READY_JSON"])
except Exception:
    print("unknown")
    raise SystemExit(0)
checks = payload.get("checks") or {}
print(checks.get("capacity", "unknown"))
PY
)"

if [ "$active_sessions" != "0" ] || [ "$capacity" = "full" ]; then
  echo "browser-runtime has ${active_sessions} active session(s); clearing stale E2E state by restarting browser-runtime."
  docker compose restart browser-runtime >/dev/null
fi

for attempt in $(seq 1 30); do
  if curl -fsS --max-time 5 "${BROWSER_RUNTIME_URL}/readyz" >/tmp/live-demo-browser-ready.json 2>/tmp/live-demo-browser-ready.err; then
    status="$(python3 - <<'PY'
import json

with open("/tmp/live-demo-browser-ready.json", encoding="utf-8") as fh:
    payload = json.load(fh)
checks = payload.get("checks") or {}
print(payload.get("status"), checks.get("capacity"), payload.get("active_sessions"))
PY
)"
    if [ "$status" = "ok ok 0" ]; then
      echo "browser-runtime ready for E2E at ${BROWSER_RUNTIME_URL}"
      exit 0
    fi
  fi
  sleep 1
done

echo "browser-runtime did not become ready for E2E."
cat /tmp/live-demo-browser-ready.err 2>/dev/null || true
cat /tmp/live-demo-browser-ready.json 2>/dev/null || true
exit 1
