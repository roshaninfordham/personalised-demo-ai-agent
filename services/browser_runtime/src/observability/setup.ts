import type { FastifyInstance } from "fastify";

import { browserMetrics } from "./metrics.js";

export function setupObservabilityRoutes(server: FastifyInstance): void {
  server.get("/metrics", async (_request, reply) => {
    return reply.type("text/plain; version=0.0.4").send(browserMetrics.renderPrometheus());
  });
}
