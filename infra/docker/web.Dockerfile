FROM node:20-slim AS base

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
RUN chown -R node:node /app

USER node

EXPOSE 3000

CMD ["pnpm", "--filter", "@live-demo-agent/web", "start"]
