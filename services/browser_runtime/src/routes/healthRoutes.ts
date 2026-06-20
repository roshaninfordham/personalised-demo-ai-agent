import type { FastifyInstance } from "fastify";

import { getHealth } from "../health.js";
import type { BrowserRuntimeDependencies } from "../server.js";

export function registerHealthRoutes(server: FastifyInstance, deps: BrowserRuntimeDependencies): void {
  server.get("/healthz", () => getHealth());
  server.get("/readyz", async () => {
    const checks: Record<string, string> = {};
    checks.redis = (await deps.redis.ping()) === "PONG" ? "ok" : "failed";
    checks.object_storage = "skipped";
    checks.playwright = (await deps.playwrightFactory.isLaunchable()) ? "ok" : "failed";
    return {
      status: Object.values(checks).includes("failed") ? "degraded" : "ok",
      service: "browser-runtime",
      version: "0.1.0",
      checks,
    };
  });
}
