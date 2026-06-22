#!/usr/bin/env bash
set -euo pipefail

images=(
  live-demo-agent/web:local
  live-demo-agent/api:local
  live-demo-agent/agent-runtime:local
  live-demo-agent/browser-runtime:local
  live-demo-agent/learner-worker:local
  live-demo-agent/post-demo-worker:local
)

scanner=""
if command -v trivy >/dev/null 2>&1; then
  scanner="trivy"
elif command -v grype >/dev/null 2>&1; then
  scanner="grype"
fi

for image in "${images[@]}"; do
  if ! docker image inspect "$image" >/dev/null 2>&1; then
    echo "Image not found, skipping vulnerability scan for $image. Run make docker-build-all first." >&2
    continue
  fi
  if [[ "$scanner" == "trivy" ]]; then
    trivy image --scanners vuln --severity CRITICAL --exit-code 1 --ignore-unfixed "$image"
  elif [[ "$scanner" == "grype" ]]; then
    grype "$image" --fail-on critical
  else
    echo "No image scanner found; verified image exists: $image"
  fi
done

echo "Image scan passed."
