import Ajv2020 from "ajv/dist/2020";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import type { BrowserActionCommand, DemoSession, LeadSummary } from "../generated/typescript/src";

const CONTRACTS_ROOT = fileURLToPath(new URL("..", import.meta.url));
const SCHEMA_DIR = join(CONTRACTS_ROOT, "schemas");

type JsonObject = Record<string, unknown>;

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function loadSchemas(): JsonObject[] {
  return readdirSync(SCHEMA_DIR)
    .filter((fileName) => fileName.endsWith(".schema.json"))
    .sort()
    .map((fileName) => {
      const parsed: unknown = JSON.parse(readFileSync(join(SCHEMA_DIR, fileName), "utf8"));

      if (!isObject(parsed)) {
        throw new Error(`${fileName} must parse to an object`);
      }

      return parsed;
    });
}

function createAjv(): Ajv2020 {
  const ajv = new Ajv2020({ allErrors: true, strict: false, validateFormats: false });
  loadSchemas().forEach((schema) => ajv.addSchema(schema));
  return ajv;
}

describe("contracts", () => {
  it("validates a sample DemoSession payload", () => {
    const payload: DemoSession = {
      session_id: "00000000-0000-4000-8000-000000000001",
      product_id: "00000000-0000-4000-8000-000000000002",
      product_url: "https://example.com",
      status: "created",
      current_phase: "created",
      created_at: "2026-06-20T00:00:00.000Z",
      updated_at: "2026-06-20T00:00:00.000Z",
    };

    const validate = createAjv().getSchema(
      "https://schemas.live-demo-agent.local/demo-session.schema.json#/$defs/DemoSession",
    );

    expect(validate?.(payload)).toBe(true);
  });

  it("validates a sample BrowserActionCommand payload", () => {
    const payload: BrowserActionCommand = {
      command_id: "00000000-0000-4000-8000-000000000003",
      session_id: "00000000-0000-4000-8000-000000000001",
      browser_session_id: "browser-session-1",
      action_type: "read_current_screen",
      created_at: "2026-06-20T00:00:00.000Z",
    };

    const validate = createAjv().getSchema(
      "https://schemas.live-demo-agent.local/browser-action.schema.json#/$defs/BrowserActionCommand",
    );

    expect(validate?.(payload)).toBe(true);
  });

  it("validates a sample LeadSummary payload", () => {
    const payload: LeadSummary = {
      lead_summary_id: "00000000-0000-4000-8000-000000000004",
      session_id: "00000000-0000-4000-8000-000000000001",
      demo_summary: {
        duration_seconds: 0,
        features_shown: [],
        questions_asked: [],
        screens_visited: [],
      },
      qualification: {
        insights: [],
        urgency_level: "unknown",
        confidence: 0,
      },
      recommended_follow_up: "Not implemented in Phase 1.",
      crm_payload: {
        provider: "mock",
        objects: [],
      },
      created_at: "2026-06-20T00:00:00.000Z",
    };

    const validate = createAjv().getSchema(
      "https://schemas.live-demo-agent.local/lead-summary.schema.json#/$defs/LeadSummary",
    );

    expect(validate?.(payload)).toBe(true);
  });
});
