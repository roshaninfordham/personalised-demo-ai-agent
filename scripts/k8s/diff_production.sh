#!/usr/bin/env bash
set -euo pipefail

scripts/k8s/render_manifests.sh production >/dev/null
kubectl diff -f .local/rendered-production.yaml
