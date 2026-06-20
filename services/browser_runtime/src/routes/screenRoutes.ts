import type { FastifyInstance } from "fastify";

import type { BrowserRuntimeDependencies } from "../server.js";

const basePath = "/internal/browser/v1";

export function registerScreenRoutes(server: FastifyInstance, deps: BrowserRuntimeDependencies): void {
  server.get(`${basePath}/sessions/:browser_session_id/screen`, async (request) => {
    const { browser_session_id: browserSessionId } = request.params as { browser_session_id: string };
    const session = deps.sessionManager.getSession(browserSessionId);
    return deps.screenReader.readCurrentScreen(session, { captureScreenshot: deps.config.browserEnableScreenshots });
  });

  server.post(`${basePath}/sessions/:browser_session_id/screenshot`, async (request) => {
    const { browser_session_id: browserSessionId } = request.params as { browser_session_id: string };
    const session = deps.sessionManager.getSession(browserSessionId);
    const screen = await deps.screenReader.readCurrentScreen(session, { captureScreenshot: true });
    return {
      screen_id: screen.screen_id,
      screenshot_uri: screen.screenshot_uri,
    };
  });
}

