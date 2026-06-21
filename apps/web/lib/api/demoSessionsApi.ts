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
  demoSessionEndpoint,
  demoSessionEndEndpoint,
  demoSessionJoinConfigEndpoint,
  demoSessionOrchestrationStateEndpoint,
  demoSessionPrewarmEndpoint,
  demoSessionRecoverEndpoint,
  demoSessionsEndpoint,
  demoSessionStartEndpoint,
  demoSessionStateEndpoint,
} from "./endpoints";

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
