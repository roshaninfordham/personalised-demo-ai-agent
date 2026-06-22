#!/usr/bin/env bash
set -euo pipefail

echo "== Docker system df =="
docker system df || true

echo
echo "== Docker builder du =="
docker builder du || true
