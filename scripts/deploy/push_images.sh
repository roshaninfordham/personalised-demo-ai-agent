#!/usr/bin/env bash
set -euo pipefail

registry="${IMAGE_REGISTRY:?IMAGE_REGISTRY is required}"
tag="${IMAGE_TAG:?IMAGE_TAG is required}"
for service in web api agent-runtime browser-runtime learner-worker post-demo-worker; do
  docker tag "live-demo-agent/${service}:${tag}" "${registry}/${service}:${tag}"
  docker push "${registry}/${service}:${tag}"
done
