FROM node:20-slim AS builder

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PNPM_HOME=/pnpm

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY tsconfig.base.json eslint.config.mjs .prettierrc.json ./
COPY apps/web/package.json apps/web/package.json
COPY services/browser_runtime/package.json services/browser_runtime/package.json
COPY packages/contracts/package.json packages/contracts/package.json

RUN pnpm install --frozen-lockfile

COPY apps/web apps/web
COPY packages/contracts packages/contracts

RUN pnpm --filter @live-demo-agent/web build

FROM node:20-slim AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

RUN apt-get update \
  && apt-get upgrade -y \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd --system --gid 10001 app \
  && useradd --system --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin app \
  && mkdir -p /app /tmp /app/.cache \
  && chown -R 10001:10001 /app /tmp

COPY --from=builder --chown=10001:10001 /app/apps/web/.next/standalone ./
COPY --from=builder --chown=10001:10001 /app/apps/web/.next/static ./apps/web/.next/static

USER 10001:10001

EXPOSE 3000

CMD ["node", "apps/web/server.js"]
