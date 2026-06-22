#!/usr/bin/env bash
set -euo pipefail

if [[ "${CONFIRM_PRODUCTION_DEPLOY:-}" != "yes" ]]; then
  echo "Set CONFIRM_PRODUCTION_DEPLOY=yes after approval to deploy production." >&2
  exit 1
fi

namespace="${K8S_NAMESPACE:-live-demo-agent}"
scripts/k8s/render_manifests.sh production >/dev/null
kubectl apply -f .local/rendered-production.yaml
scripts/deploy/wait_for_rollout.sh "$namespace" web api agent-runtime browser-runtime
echo "Production deployment completed."
