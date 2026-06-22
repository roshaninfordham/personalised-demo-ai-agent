#!/usr/bin/env bash
set -euo pipefail

namespace="${K8S_NAMESPACE:-live-demo-agent-staging}"
scripts/k8s/render_manifests.sh staging >/dev/null
kubectl apply -f .local/rendered-staging.yaml
scripts/deploy/wait_for_rollout.sh "$namespace" web-staging api-staging agent-runtime-staging browser-runtime-staging
echo "Staging deployment completed."
