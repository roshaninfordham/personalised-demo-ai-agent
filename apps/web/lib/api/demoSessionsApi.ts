import type {
  CreateDemoSessionRequest,
  CreateDemoSessionResponse,
  DemoSessionResponse,
  DemoSessionStateResponse,
  JoinConfigResponse,
  StartDemoSessionResponse,
} from "@live-demo-agent/contracts";

import { apiRequest } from "./apiClient";
import {
  demoStartEndpoint,
  demoSessionEndpoint,
  demoSessionEndEndpoint,
  demoSessionJoinConfigEndpoint,
  demoSessionOrchestrationStateEndpoint,
  demoSessionPrewarmEndpoint,
  demoSessionRecoverEndpoint,
  demoSessionsEndpoint,
  demoSessionStartEndpoint,
  demoSessionStateEndpoint,
  demoSessionTextTurnEndpoint,
} from "./endpoints";

export type StartDemoRequest = {
  product_url: string;
  product_name?: string | null;
  target_persona?: string | null;
  text_guidance?: string | null;
};

export type StartDemoResponse = {
  session_id: string;
  status: string;
  redirect_url: string;
};

export function startDemo(request: StartDemoRequest): Promise<StartDemoResponse> {
  return apiRequest<StartDemoResponse>(demoStartEndpoint(), {
    method: "POST",
    body: request,
    timeoutMs: 30_000,
  });
}

export function createDemoSession(request: CreateDemoSessionRequest): Promise<CreateDemoSessionResponse> {
  return apiRequest<CreateDemoSessionResponse>(demoSessionsEndpoint(), { method: "POST", body: request });
}

export function startDemoSession(sessionId: string): Promise<StartDemoSessionResponse> {
  return apiRequest<StartDemoSessionResponse>(demoSessionStartEndpoint(sessionId), { method: "POST", body: {} });
}

export function prewarmDemoSession(sessionId: string): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(demoSessionPrewarmEndpoint(sessionId), { method: "POST", body: {} });
}

export function endDemoSession(sessionId: string, reason = "user_ended"): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(demoSessionEndEndpoint(sessionId), { method: "POST", body: { reason } });
}

export function recoverDemoSession(sessionId: string, reasonCode = "unknown"): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(demoSessionRecoverEndpoint(sessionId), {
    method: "POST",
    body: { reason_code: reasonCode },
  });
}

export function getDemoSession(sessionId: string): Promise<DemoSessionResponse> {
  return apiRequest<DemoSessionResponse>(demoSessionEndpoint(sessionId));
}

export function getOrchestrationState(sessionId: string): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(demoSessionOrchestrationStateEndpoint(sessionId));
}

export function getDemoSessionState(sessionId: string): Promise<DemoSessionStateResponse> {
  return apiRequest<DemoSessionStateResponse>(demoSessionStateEndpoint(sessionId));
}

export function getJoinConfig(sessionId: string): Promise<JoinConfigResponse> {
  return apiRequest<JoinConfigResponse>(demoSessionJoinConfigEndpoint(sessionId));
}

export type TextTurnResponse = {
  turn_id: string;
  assistant_response: string;
  action_taken: string | null;
  policy_blocked: boolean;
  agent_phase?: string | null;
};

export function sendTextTurn(sessionId: string, text: string): Promise<TextTurnResponse> {
  return apiRequest<TextTurnResponse>(demoSessionTextTurnEndpoint(sessionId), {
    method: "POST",
    body: { text },
    timeoutMs: 30_000,
  });
}
