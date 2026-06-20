import type {
  CreateDemoSessionRequest,
  CreateDemoSessionResponse,
} from "@live-demo-agent/contracts";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function getApiHealth(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_BASE_URL}/healthz`);

  if (!response.ok) {
    throw new Error(`API health check failed with status ${String(response.status)}`);
  }

  return response.json() as Promise<{ status: string; service: string }>;
}

export function createDemoSession(
  request: CreateDemoSessionRequest,
): Promise<CreateDemoSessionResponse> {
  void request;
  return Promise.reject(new Error("Demo session creation is not implemented in Phase 1."));
}
