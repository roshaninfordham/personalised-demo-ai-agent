#!/usr/bin/env bash
set -euo pipefail

scripts/k8s/render_manifests.sh staging >/dev/null
kubectl diff -f .local/rendered-staging.yaml
