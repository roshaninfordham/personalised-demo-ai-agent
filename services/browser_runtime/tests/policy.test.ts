import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import {
  DeterministicActionSafetyPolicy,
  type ActionPolicyRequest,
} from "../src/policy/actionPolicy.js";
import { hasPermission } from "../src/policy/rbacClient.js";
import { redactJson, redactScreenshotMetadata, redactText } from "../src/policy/redaction.js";

const fixturesDir = resolve(process.cwd(), "../../packages/policies/fixtures");
const organizationId = "00000000-0000-0000-0000-000000000001";
const sessionId = "00000000-0000-0000-0000-000000000010";

function loadFixture(name: string): Record<string, unknown> {
  return JSON.parse(readFileSync(resolve(fixturesDir, name), "utf8")) as Record<string, unknown>;
}

function actionRequest(fixture: Record<string, unknown>): ActionPolicyRequest {
  const raw = fixture.request as Record<string, unknown>;
  return {
    organization_id: organizationId,
    session_id: sessionId,
    actor: { actor_type: "agent", actor_id: "agent-runtime", role: "agent_runtime" },
    action_type: String(raw.action_type),
    action_label: raw.action_label as string | null,
    element_role: raw.element_role as string | null,
    element_label: raw.element_label as string | null,
    element_text: raw.element_text as string | null,
    surrounding_text: raw.surrounding_text as string | null,
    input_type: raw.input_type as string | null,
    current_url: raw.current_url as string | null,
    target_url: raw.target_url as string | null,
    allowed_domains: Array.isArray(raw.allowed_domains) ? (raw.allowed_domains as string[]) : [],
    recipe_never_click: Array.isArray(raw.recipe_never_click)
      ? (raw.recipe_never_click as string[])
      : [],
    trace_id: "trace-test",
  };
}

describe("shared policy fixtures", () => {
  it("matches action policy fixtures", () => {
    const policy = new DeterministicActionSafetyPolicy();
    for (const file of readdirSync(fixturesDir).filter((name) => name.startsWith("action_"))) {
      const fixture = loadFixture(file);
      const expected = fixture.expected as Record<string, string>;
      const decision = policy.evaluate(actionRequest(fixture));
      expect(decision.decision).toBe(expected.decision);
      expect(decision.risk_level).toBe(expected.risk_level);
      expect(decision.reason_codes).toContain(expected.reason_code);
    }
  });

  it("matches recipe never-click fixture", () => {
    const fixture = loadFixture("recipe_never_click_override.json");
    const decision = new DeterministicActionSafetyPolicy().evaluate(actionRequest(fixture));
    expect(decision.decision).toBe("blocked");
    expect(decision.reason_codes).toContain("recipe_never_click_match");
  });
});

describe("browser policy helpers", () => {
  it("checks RBAC from generated policy rules", () => {
    expect(hasPermission("owner", "crm:export")).toBe(true);
    expect(hasPermission("viewer", "recipe:activate")).toBe(false);
    expect(hasPermission("agent_runtime", "browser:execute_medium")).toBe(true);
    expect(hasPermission("agent_runtime", "crm:export")).toBe(false);
  });

  it("redacts text and json metadata", () => {
    expect(redactText("Contact alice@example.com").redactedValue).toBe(
      "Contact [REDACTED_EMAIL]",
    );
    expect(redactText("card 4242 4242 4242 4242").redactedValue).toBe(
      "card [REDACTED_CREDIT_CARD]",
    );
    expect(redactJson({ api_key: "secret", nested: { email: "a@example.com" } }).redactedValue).toEqual({
      api_key: "[REDACTED_SECRET]",
      nested: { email: "[REDACTED_EMAIL]" },
    });
  });

  it("marks screenshot metadata as text-only redacted", () => {
    const result = redactScreenshotMetadata({ visible_text: "alice@example.com" });
    expect(result.visible_text).toBe("[REDACTED_EMAIL]");
    expect(result.text_metadata_redacted).toBe(true);
    expect(result.visual_redaction_applied).toBe(false);
  });
});
