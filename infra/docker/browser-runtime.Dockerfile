FROM mcr.microsoft.com/playwright:v1.61.0-noble AS base

ENV NODE_ENV=production

WORKDIR /app

RUN npm install -g pnpm@10.30.1

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY tsconfig.base.json eslint.config.mjs .prettierrc.json ./
COPY services/browser_runtime/package.json services/browser_runtime/package.json
COPY packages/contracts/package.json packages/contracts/package.json
COPY packages/policies/package.json packages/policies/package.json

RUN pnpm install --frozen-lockfile --prod=false

COPY services/browser_runtime services/browser_runtime
COPY packages/contracts packages/contracts
COPY packages/policies packages/policies

RUN pnpm --filter @live-demo-agent/browser-runtime build
RUN chown -R pwuser:pwuser /app

ENV NODE_ENV=production

USER pwuser

EXPOSE 8200

CMD ["node", "services/browser_runtime/dist/src/index.js"]
