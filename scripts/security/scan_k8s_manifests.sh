#!/usr/bin/env bash
set -euo pipefail

scripts/k8s/validate_manifests.sh

if command -v checkov >/dev/null 2>&1; then
  checkov -d infra/k8s --config-file infra/security/checkov.yaml
else
  echo "checkov not found; skipped optional IaC scan."
fi

if command -v kube-linter >/dev/null 2>&1; then
  kube-linter lint infra/k8s --config infra/security/kube-linter.yaml
else
  echo "kube-linter not found; skipped optional kube-linter scan."
fi

echo "Kubernetes manifest security scan passed."
