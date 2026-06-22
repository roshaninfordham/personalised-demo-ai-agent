#!/usr/bin/env bash
set -euo pipefail

echo "== Tool versions =="
docker --version || true
docker compose version || true
node --version || true
pnpm --version || true
python --version || true
uv --version || true

echo
echo "== Compose status =="
docker compose ps || true

echo
scripts/dev/docker_disk_usage.sh

echo
echo "== Local health =="
scripts/dev/health_check.sh || true
