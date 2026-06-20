FROM node:20-slim AS base

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY tsconfig.base.json eslint.config.mjs .prettierrc.json ./
COPY apps/web/package.json apps/web/package.json
COPY services/browser_runtime/package.json services/browser_runtime/package.json
COPY packages/contracts/package.json packages/contracts/package.json

RUN pnpm install --frozen-lockfile

COPY services/browser_runtime services/browser_runtime
COPY packages/contracts packages/contracts

RUN pnpm --filter @live-demo-agent/browser-runtime build
RUN chown -R node:node /app

USER node

EXPOSE 8010

CMD ["node", "services/browser_runtime/dist/src/index.js"]
