import type { FastifyInstance } from "fastify";

import { navigateSession } from "../browser/navigation.js";
import { parseBody, navigateRequestSchema } from "../contracts/validators.js";
import type { BrowserRuntimeDependencies } from "../server.js";

const basePath = "/internal/browser/v1";

export function registerNavigationRoutes(
  server: FastifyInstance,
  deps: BrowserRuntimeDependencies,
): void {
  server.post(`${basePath}/sessions/:browser_session_id/navigate`, async (request) => {
    const { browser_session_id: browserSessionId } = request.params as { browser_session_id: string };
    const body = parseBody(navigateRequestSchema, request.body);
    const session = deps.sessionManager.getSession(browserSessionId);
    const result = await navigateSession(session, body.url, deps.config, deps.events, deps.screenReader);
    await deps.liveState.setBrowserStatus(session);
    return { ...result, screen_state: session.currentScreenState };
  });
}

