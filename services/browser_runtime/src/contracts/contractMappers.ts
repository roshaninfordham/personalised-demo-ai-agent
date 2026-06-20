import type {
  BrowserActionCommand,
  BrowserActionResult,
  BrowserActionType,
  RiskLevel,
} from "@live-demo-agent/contracts";

export type ActionRequestBody = {
  command_id?: string | undefined;
  session_id?: string | undefined;
  action_type?: BrowserActionType | undefined;
  element_id?: string | undefined;
  text?: string | undefined;
  direction?: "up" | "down" | "left" | "right" | undefined;
  url?: string | undefined;
  requires_cursor_animation?: boolean | undefined;
  policy_context?: Record<string, unknown> | undefined;
  user_confirmed?: boolean | undefined;
};

export function toBrowserActionCommand(
  body: ActionRequestBody,
  actionType: BrowserActionType,
  browserSessionId: string,
  demoSessionId: string,
  commandId: string,
): BrowserActionCommand {
  const command: BrowserActionCommand = {
    command_id: body.command_id ?? commandId,
    session_id: body.session_id ?? demoSessionId,
    browser_session_id: browserSessionId,
    action_type: body.action_type ?? actionType,
    created_at: new Date().toISOString(),
    requires_cursor_animation: body.requires_cursor_animation ?? true,
    policy_context: {
      ...(body.policy_context ?? {}),
      user_confirmed: body.user_confirmed ?? false,
    },
  };
  if (body.element_id !== undefined) command.element_id = body.element_id;
  if (body.text !== undefined) command.text = body.text;
  if (body.direction !== undefined) command.direction = body.direction;
  if (body.url !== undefined) command.url = body.url;
  return command;
}

export function failedActionResult(
  command: BrowserActionCommand,
  riskLevel: RiskLevel,
  code: string,
  message: string,
  latencyMs: number,
): BrowserActionResult {
  return {
    command_id: command.command_id,
    session_id: command.session_id,
    success: false,
    policy_decision: "blocked",
    risk_level: riskLevel,
    latency_ms: latencyMs,
    created_at: new Date().toISOString(),
    error_code: code,
    error_message: message,
  };
}
