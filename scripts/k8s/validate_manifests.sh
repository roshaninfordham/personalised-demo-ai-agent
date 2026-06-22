#!/usr/bin/env bash
set -euo pipefail

scripts/k8s/render_manifests.sh staging >/dev/null
scripts/k8s/render_manifests.sh production >/dev/null

for rendered in .local/rendered-staging.yaml .local/rendered-production.yaml; do
  if [[ ! -s "$rendered" ]]; then
    echo "Rendered manifest is empty: $rendered" >&2
    exit 1
  fi
  if command -v kubeconform >/dev/null 2>&1; then
    kubeconform -strict -summary -ignore-missing-schemas "$rendered"
  else
    grep -q '^apiVersion:' "$rendered"
    grep -q '^kind:' "$rendered"
    echo "kubeconform not found; structural validation passed for $rendered."
  fi
done

echo "Kubernetes manifests validate."
