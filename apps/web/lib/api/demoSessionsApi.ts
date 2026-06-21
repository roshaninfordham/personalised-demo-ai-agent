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
  demoSessionJoinConfigEndpoint,
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

export function getDemoSession(sessionId: string): Promise<DemoSessionResponse> {
  return apiRequest<DemoSessionResponse>(demoSessionEndpoint(sessionId));
}

export function getDemoSessionState(sessionId: string): Promise<DemoSessionStateResponse> {
  return apiRequest<DemoSessionStateResponse>(demoSessionStateEndpoint(sessionId));
}

export function getJoinConfig(sessionId: string): Promise<JoinConfigResponse> {
  return apiRequest<JoinConfigResponse>(demoSessionJoinConfigEndpoint(sessionId));
}
