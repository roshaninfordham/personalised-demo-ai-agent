#!/usr/bin/env bash
set -euo pipefail

pnpm exec playwright test -c tests/e2e/playwright.config.ts tests/e2e/user-demo.spec.ts --headed
