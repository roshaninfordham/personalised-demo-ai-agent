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
  uid="$(docker run --rm --entrypoint /usr/bin/id "$image" -u)"
  if [[ "$uid" == "0" ]]; then
    echo "$image runs as root." >&2
    exit 1
  fi
  echo "$image runs as UID $uid"
done
