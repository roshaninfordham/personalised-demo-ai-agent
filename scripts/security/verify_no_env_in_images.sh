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

for image in "${images[@]}"; do
  docker image inspect "$image" >/dev/null
  if docker run --rm --entrypoint /bin/sh "$image" -c 'find /app -name ".env" -o -name ".env.*" | grep .' ; then
    echo ".env file found in $image" >&2
    exit 1
  fi
done

echo "No .env files found in application images."
