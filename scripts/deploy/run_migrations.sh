#!/usr/bin/env bash
set -euo pipefail

environment="${1:-staging}"
namespace="${K8S_NAMESPACE:-live-demo-agent}"
scripts/k8s/render_manifests.sh "$environment" >/dev/null
kubectl -n "$namespace" apply -f .local/rendered-${environment}.yaml --selector app.kubernetes.io/name=db-migrate
kubectl -n "$namespace" wait --for=condition=complete job/db-migrate --timeout=180s
