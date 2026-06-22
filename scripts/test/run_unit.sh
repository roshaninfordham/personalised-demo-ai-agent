#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local/test-results
uv run pytest tests/unit services/api/tests services/agent_runtime/tests services/learner_worker/tests \
  -m "not integration" \
  --junitxml=.local/test-results/unit-results.xml
pnpm test
