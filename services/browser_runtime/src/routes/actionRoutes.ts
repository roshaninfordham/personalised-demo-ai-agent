import { randomUUID } from "node:crypto";

import type { FastifyInstance } from "fastify";
import type { BrowserActionType } from "@live-demo-agent/contracts";

import { parseBody, actionRequestSchema } from "../contracts/validators.js";
import { toBrowserActionCommand } from "../contracts/contractMappers.js";
import type { BrowserRuntimeDependencies } from "../server.js";

const basePath = "/internal/browser/v1";
const actionTypes: BrowserActionType[] = [
  "read_current_screen",
  "highlight_element",
  "click_element",
  "type_into_element",
  "scroll",
  "go_back",
  "navigate_to_allowed_url",
  "wait_for_idle",
];

export function registerActionRoutes(server: FastifyInstance, deps: BrowserRuntimeDependencies): void {
  for (const actionType of actionTypes) {
    const pathAction = actionType === "navigate_to_allowed_url" ? "navigate" : actionType;
    server.post(`${basePath}/sessions/:browser_session_id/actions/${pathAction}`, async (request) => {
      const { browser_session_id: browserSessionId } = request.params as { browser_session_id: string };
      const session = deps.sessionManager.getSession(browserSessionId);
      const body = parseBody(actionRequestSchema, request.body ?? {});
      const command = toBrowserActionCommand(
        body,
        actionType,
        browserSessionId,
        session.demoSessionId,
        randomUUID(),
      );
      return deps.actionExecutor.execute(session, command);
    });
  }

  server.post(`${basePath}/sessions/:browser_session_id/actions/execute`, async (request) => {
    const { browser_session_id: browserSessionId } = request.params as { browser_session_id: string };
    const session = deps.sessionManager.getSession(browserSessionId);
    const body = parseBody(actionRequestSchema, request.body);
    const command = toBrowserActionCommand(
      body,
      body.action_type ?? "read_current_screen",
      browserSessionId,
      session.demoSessionId,
      randomUUID(),
    );
    return deps.actionExecutor.execute(session, command);
  });
}

