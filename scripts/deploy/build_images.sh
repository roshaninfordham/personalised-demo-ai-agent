#!/usr/bin/env bash
set -euo pipefail

tag="${IMAGE_TAG:-local}"
docker build -f infra/docker/web.Dockerfile -t "live-demo-agent/web:${tag}" .
docker build -f infra/docker/api.Dockerfile -t "live-demo-agent/api:${tag}" .
docker build -f infra/docker/agent-runtime.Dockerfile -t "live-demo-agent/agent-runtime:${tag}" .
docker build -f infra/docker/browser-runtime.Dockerfile -t "live-demo-agent/browser-runtime:${tag}" .
docker build -f infra/docker/learner-worker.Dockerfile -t "live-demo-agent/learner-worker:${tag}" .
docker build -f infra/docker/post-demo-worker.Dockerfile -t "live-demo-agent/post-demo-worker:${tag}" .
