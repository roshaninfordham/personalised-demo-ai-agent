// Generated from packages/contracts/schemas. Do not edit manually.

import type { BoundingBox, DemoPhase, IsoDateTimeString, JsonValue, Metadata, PolicyDecision, ProviderName, RiskLevel, SessionStatus, TraceId, UuidString } from "./common";

export interface LearnerJobEnvelope {
  job_id: string;
  organization_id: string;
  product_id: string;
  session_id?: string | null;
  learning_run_id: string;
  job_type: "learn_product_from_url" | "summarize_first_screen" | "explore_candidate_actions" | "build_demo_graph" | "generate_demo_route" | "chunk_product_knowledge" | "embed_knowledge_chunks" | "refresh_product_learning";
  start_url: string;
  priority?: number;
  attempt: number;
  max_attempts: number;
  created_at: string;
  trace_id: string;
  payload?: Record<string, JsonValue>;
}
