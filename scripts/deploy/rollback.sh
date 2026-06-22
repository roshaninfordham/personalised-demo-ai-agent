#!/usr/bin/env bash
set -euo pipefail

environment="${1:-staging}"
namespace="${K8S_NAMESPACE:-live-demo-agent}"
if [[ "$environment" == "staging" ]]; then
  namespace="${K8S_NAMESPACE:-live-demo-agent-staging}"
fi

for deployment in web api agent-runtime browser-runtime learner-worker post-demo-worker; do
  kubectl -n "$namespace" rollout undo "deployment/${deployment}" || true
done
echo "Rollback requested for $environment. Database schema rollback is manual and must be verified separately."
