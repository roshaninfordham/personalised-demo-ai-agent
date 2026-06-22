#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local/test-results
uv run pytest tests/integration services/api/tests services/agent_runtime/tests services/learner_worker/tests \
  -m integration \
  --junitxml=.local/test-results/integration-results.xml
pnpm --filter @live-demo-agent/browser-runtime test:integration
