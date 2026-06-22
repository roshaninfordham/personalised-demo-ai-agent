FROM node:20-slim AS base-node

ENV NODE_ENV=production \
    PNPM_HOME=/pnpm

WORKDIR /app

RUN corepack enable \
  && groupadd --system --gid 10001 app \
  && useradd --system --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin app \
  && mkdir -p /app /tmp /app/.cache /pnpm \
  && chown -R 10001:10001 /app /tmp /pnpm
