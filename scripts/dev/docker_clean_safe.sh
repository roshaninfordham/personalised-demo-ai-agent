#!/usr/bin/env bash
set -euo pipefail

echo "Safe Docker cleanup: pruning builder cache older than 24h, dangling images, and stopped containers."
docker builder prune --filter until=24h --keep-storage 10GB -f
docker image prune -f
docker container prune -f
