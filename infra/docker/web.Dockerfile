FROM node:20-slim AS builder

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PNPM_HOME=/pnpm

WORKDIR /app

RUN corepack enable

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_EVENTS_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_BROWSER_RUNTIME_URL=http://localhost:8200
ARG NEXT_PUBLIC_AGENT_RUNTIME_URL=http://localhost:8300
ARG NEXT_PUBLIC_MINIO_URL=http://localhost:9000
ARG NEXT_PUBLIC_GRAFANA_URL=http://localhost:3001
ARG NEXT_PUBLIC_PROMETHEUS_URL=http://localhost:9090
ARG NEXT_PUBLIC_JAEGER_URL=http://localhost:16686
ARG NEXT_PUBLIC_LOKI_URL=http://localhost:3100
ARG NEXT_PUBLIC_PROVIDER_MODE_LABEL="Fake Providers"

ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_EVENTS_BASE_URL=$NEXT_PUBLIC_EVENTS_BASE_URL \
    NEXT_PUBLIC_BROWSER_RUNTIME_URL=$NEXT_PUBLIC_BROWSER_RUNTIME_URL \
    NEXT_PUBLIC_AGENT_RUNTIME_URL=$NEXT_PUBLIC_AGENT_RUNTIME_URL \
    NEXT_PUBLIC_MINIO_URL=$NEXT_PUBLIC_MINIO_URL \
    NEXT_PUBLIC_GRAFANA_URL=$NEXT_PUBLIC_GRAFANA_URL \
    NEXT_PUBLIC_PROMETHEUS_URL=$NEXT_PUBLIC_PROMETHEUS_URL \
    NEXT_PUBLIC_JAEGER_URL=$NEXT_PUBLIC_JAEGER_URL \
    NEXT_PUBLIC_LOKI_URL=$NEXT_PUBLIC_LOKI_URL \
    NEXT_PUBLIC_PROVIDER_MODE_LABEL=$NEXT_PUBLIC_PROVIDER_MODE_LABEL

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY tsconfig.base.json eslint.config.mjs .prettierrc.json ./
COPY apps/web/package.json apps/web/package.json
COPY services/browser_runtime/package.json services/browser_runtime/package.json
COPY packages/contracts/package.json packages/contracts/package.json

RUN --mount=type=cache,target=/pnpm/store \
  pnpm install --frozen-lockfile

COPY apps/web apps/web
COPY packages/contracts packages/contracts

RUN pnpm --filter @live-demo-agent/web build

FROM node:20-slim AS runtime

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_EVENTS_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_BROWSER_RUNTIME_URL=http://localhost:8200
ARG NEXT_PUBLIC_AGENT_RUNTIME_URL=http://localhost:8300
ARG NEXT_PUBLIC_MINIO_URL=http://localhost:9000
ARG NEXT_PUBLIC_GRAFANA_URL=http://localhost:3001
ARG NEXT_PUBLIC_PROMETHEUS_URL=http://localhost:9090
ARG NEXT_PUBLIC_JAEGER_URL=http://localhost:16686
ARG NEXT_PUBLIC_LOKI_URL=http://localhost:3100
ARG NEXT_PUBLIC_PROVIDER_MODE_LABEL="Fake Providers"

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_EVENTS_BASE_URL=$NEXT_PUBLIC_EVENTS_BASE_URL \
    NEXT_PUBLIC_BROWSER_RUNTIME_URL=$NEXT_PUBLIC_BROWSER_RUNTIME_URL \
    NEXT_PUBLIC_AGENT_RUNTIME_URL=$NEXT_PUBLIC_AGENT_RUNTIME_URL \
    NEXT_PUBLIC_MINIO_URL=$NEXT_PUBLIC_MINIO_URL \
    NEXT_PUBLIC_GRAFANA_URL=$NEXT_PUBLIC_GRAFANA_URL \
    NEXT_PUBLIC_PROMETHEUS_URL=$NEXT_PUBLIC_PROMETHEUS_URL \
    NEXT_PUBLIC_JAEGER_URL=$NEXT_PUBLIC_JAEGER_URL \
    NEXT_PUBLIC_LOKI_URL=$NEXT_PUBLIC_LOKI_URL \
    NEXT_PUBLIC_PROVIDER_MODE_LABEL=$NEXT_PUBLIC_PROVIDER_MODE_LABEL

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
