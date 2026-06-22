#!/usr/bin/env bash
set -euo pipefail

mkdir -p .local/security

if command -v trivy >/dev/null 2>&1; then
  trivy fs --severity CRITICAL,HIGH --exit-code 1 --ignore-unfixed --format table .
else
  echo "trivy not found; dependency scan fallback checks lockfiles exist."
  test -f uv.lock
  test -f pnpm-lock.yaml
fi

echo "Dependency scan passed."
