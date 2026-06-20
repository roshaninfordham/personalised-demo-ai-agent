import type { FastifyInstance } from "fastify";

import { parseBody, createBrowserSessionRequestSchema } from "../contracts/validators.js";
import type { BrowserRuntimeDependencies } from "../server.js";

const basePath = "/internal/browser/v1";

export function registerBrowserSessionRoutes(
  server: FastifyInstance,
  deps: BrowserRuntimeDependencies,
): void {
  server.post(`${basePath}/sessions`, async (request, reply) => {
    const body = parseBody(createBrowserSessionRequestSchema, request.body);
    const input = {
      organizationId: body.organization_id,
      demoSessionId: body.demo_session_id,
      productId: body.product_id,
      viewport: body.viewport ?? {
        width: deps.config.browserViewportWidth,
        height: deps.config.browserViewportHeight,
      },
      allowedDomains: body.allowed_domains ?? [],
    };
    const session = await deps.sessionManager.createSession(
      body.start_url === undefined ? input : { ...input, startUrl: body.start_url },
    );
    return reply.status(201).send({
      browser_session_id: session.browserSessionId,
      status: session.status,
      created_at: session.createdAt,
    });
  });

  server.get(`${basePath}/sessions/:browser_session_id`, (request) => {
    const { browser_session_id: browserSessionId } = request.params as { browser_session_id: string };
    const session = deps.sessionManager.getSession(browserSessionId);
    return {
      browser_session_id: session.browserSessionId,
      organization_id: session.organizationId,
      demo_session_id: session.demoSessionId,
      product_id: session.productId,
      status: session.status,
      created_at: session.createdAt,
      updated_at: session.updatedAt,
      expires_at: session.expiresAt,
      current_url: session.page.url(),
    };
  });

  server.delete(`${basePath}/sessions/:browser_session_id`, async (request) => {
    const { browser_session_id: browserSessionId } = request.params as { browser_session_id: string };
    await deps.sessionManager.closeSession(browserSessionId);
    return { status: "closed", browser_session_id: browserSessionId };
  });
}
