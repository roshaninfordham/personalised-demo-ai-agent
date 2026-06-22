#!/usr/bin/env bash
set -euo pipefail

environment="${1:-staging}"
overlay="infra/k8s/overlays/${environment}"
mkdir -p .local

if [[ ! -d "$overlay" ]]; then
  echo "Unknown overlay: $environment" >&2
  exit 1
fi

if command -v kustomize >/dev/null 2>&1; then
  kustomize build "$overlay" > ".local/rendered-${environment}.yaml"
elif command -v kubectl >/dev/null 2>&1; then
  kubectl kustomize "$overlay" > ".local/rendered-${environment}.yaml"
else
  echo "Neither kustomize nor kubectl found; concatenating base manifests as structural fallback." >&2
  find infra/k8s/base -name '*.yaml' -type f | sort | xargs cat > ".local/rendered-${environment}.yaml"
fi

echo ".local/rendered-${environment}.yaml"
