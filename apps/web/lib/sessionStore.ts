import type { DemoSession } from "@live-demo-agent/contracts";

export function createInitialSessionState(sessionId: string): DemoSession {
  const now = new Date().toISOString();

  return {
    session_id: sessionId,
    product_id: "local-dev-product",
    start_url: "http://localhost:3000",
    status: "created",
    current_phase: "created",
    created_at: now,
    updated_at: now,
  };
}
