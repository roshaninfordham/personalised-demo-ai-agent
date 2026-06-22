#!/usr/bin/env bash
set -euo pipefail

if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --config infra/security/gitleaks.toml --redact --no-banner
else
  echo "gitleaks not found; using fixture/source secret fallback scanner."
fi

uv run python scripts/test/check_no_secrets_in_fixtures.py

if grep -RInE '(sk-[A-Za-z0-9]{20,}|nvapi-[A-Za-z0-9_-]{20,}|AWS_ACCESS_KEY_ID=A[K]IA|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----)' \
  --exclude=scan_secrets.sh --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.local .; then
  echo "Secret-like content found in repository." >&2
  exit 1
fi

echo "Secret scan passed."
