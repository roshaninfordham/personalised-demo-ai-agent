#!/usr/bin/env bash
set -euo pipefail

url="${1:-http://localhost:3000}"
if command -v open >/dev/null 2>&1; then
  open "$url"
else
  echo "$url"
fi
