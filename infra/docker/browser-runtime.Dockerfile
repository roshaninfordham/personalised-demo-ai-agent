FROM mcr.microsoft.com/playwright:v1.61.0-noble AS builder

ENV NODE_ENV=production \
    PNPM_HOME=/pnpm

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY tsconfig.base.json eslint.config.mjs .prettierrc.json ./
COPY services/browser_runtime/package.json services/browser_runtime/package.json
COPY packages/contracts/package.json packages/contracts/package.json
COPY packages/policies/package.json packages/policies/package.json

RUN pnpm install --frozen-lockfile

COPY services/browser_runtime services/browser_runtime
COPY packages/contracts packages/contracts
COPY packages/policies packages/policies

RUN pnpm --filter @live-demo-agent/browser-runtime build \
  && pnpm --filter @live-demo-agent/browser-runtime deploy --prod --legacy /browser-runtime-prod \
  && rm -rf \
    /browser-runtime-prod/src \
    /browser-runtime-prod/tests \
    /browser-runtime-prod/dist/tests \
    /browser-runtime-prod/playwright.config.ts \
    /browser-runtime-prod/vitest.integration.config.ts \
    /browser-runtime-prod/tsconfig.json \
    /browser-runtime-prod/README.md \
    /browser-runtime-prod/node_modules/.pnpm/*/node_modules/@live-demo-agent/*/tests \
    /browser-runtime-prod/node_modules/.pnpm/*/node_modules/@live-demo-agent/*/scripts \
    /browser-runtime-prod/node_modules/.pnpm/*/node_modules/@live-demo-agent/*/fixtures \
    /browser-runtime-prod/node_modules/.pnpm/*/node_modules/@live-demo-agent/*/schemas \
    /browser-runtime-prod/node_modules/.pnpm/*/node_modules/@live-demo-agent/*/pyproject.toml \
    /browser-runtime-prod/node_modules/.pnpm/*/node_modules/@live-demo-agent/*/tsconfig.json \
    /browser-runtime-prod/node_modules/.pnpm/*/node_modules/@live-demo-agent/*/README.md \
  && node -e "const fs=require('fs'); for (const file of process.argv.slice(1)) { const p=JSON.parse(fs.readFileSync(file,'utf8')); delete p.devDependencies; delete p.scripts; delete p.types; fs.writeFileSync(file, JSON.stringify(p, null, 2)); }" \
    /browser-runtime-prod/package.json \
    /browser-runtime-prod/node_modules/.pnpm/@live-demo-agent+contracts@file+packages+contracts/node_modules/@live-demo-agent/contracts/package.json \
    /browser-runtime-prod/node_modules/.pnpm/@live-demo-agent+policies@file+packages+policies/node_modules/@live-demo-agent/policies/package.json

FROM mcr.microsoft.com/playwright:v1.61.0-noble AS runtime

ENV NODE_ENV=production \
    BROWSER_CHROMIUM_NO_SANDBOX=false \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

RUN apt-get update \
  && apt-get upgrade -y \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd --system --gid 10001 app \
  && useradd --system --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin app \
  && mkdir -p /app /tmp /app/.cache /playwright-cache \
  && chown -R 10001:10001 /app /tmp /app/.cache /playwright-cache /ms-playwright

COPY --from=builder --chown=10001:10001 /browser-runtime-prod /app

USER 10001:10001

EXPOSE 8200

CMD ["node", "services/browser_runtime/dist/src/index.js"]
