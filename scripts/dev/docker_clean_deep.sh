#!/usr/bin/env bash
set -euo pipefail

echo "WARNING: This removes unused containers, networks, images, volumes, and build cache."
echo "It can free significant disk space, but the next build will be slower and local volumes may be deleted."
docker system prune -a --volumes
