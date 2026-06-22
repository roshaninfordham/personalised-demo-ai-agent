#!/usr/bin/env bash
set -euo pipefail

namespace="${1:-live-demo-agent}"
shift || true
deployments=("${@:-web api agent-runtime browser-runtime learner-worker post-demo-worker}")

for deployment in "${deployments[@]}"; do
  kubectl -n "$namespace" rollout status "deployment/${deployment}" --timeout=180s
done
