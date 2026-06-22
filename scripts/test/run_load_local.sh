#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local/load-results
if command -v locust >/dev/null 2>&1; then
  locust -f tests/load/locustfile.py --headless -u 5 -r 1 -t 5m \
    --csv .local/load-results/locust \
    --html .local/load-results/locust.html
else
  uv run python scripts/test/run_locust_fallback.py
fi
