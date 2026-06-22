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
    checks.capacity =
      deps.sessionManager.activeCount() < deps.config.browserMaxConcurrentSessions ? "ok" : "full";
    return {
      status: Object.values(checks).some((value) => value === "failed" || value === "full")
        ? "degraded"
        : "ok",
      service: "browser-runtime",
      version: "0.1.0",
      checks,
      active_sessions: deps.sessionManager.activeCount(),
      max_sessions: deps.config.browserMaxConcurrentSessions,
    };
  });
}
