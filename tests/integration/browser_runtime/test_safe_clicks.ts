import { afterEach, beforeEach, describe, expect, it } from "vitest";

import type { BrowserActionCommand } from "@live-demo-agent/contracts";
import { navigateSession } from "../../../services/browser_runtime/src/browser/navigation.js";
import { buildTestRuntime, createTestSession, startFixtureServer, type TestRuntime } from "../../../services/browser_runtime/tests/testHelpers.js";

let runtime: TestRuntime;
let fixture: Awaited<ReturnType<typeof startFixtureServer>>;

beforeEach(async () => {
  runtime = buildTestRuntime();
  fixture = await startFixtureServer();
});

afterEach(async () => {
  await runtime.shutdown();
  await fixture.close();
});

describe("safe and risky clicks", () => {
  it("executes safe Add Metric clicks and blocks risky controls", async () => {
    const session = await createTestSession(runtime, fixture.origin);
    await navigateSession(session, `${fixture.origin}/simple-dashboard.html`, runtime.config, runtime.events, runtime.screenReader);
    const addMetric = [...session.currentElements.values()].find((element) => element.label === "Add Metric");
    expect(addMetric).toBeDefined();
    const addMetricId = addMetric?.element_id;
    if (!addMetricId) throw new Error("missing Add Metric");

    const result = await runtime.actionExecutor.execute(session, command(session.browserSessionId, "click_element", { element_id: addMetricId }));
    expect(result.success).toBe(true);

    await navigateSession(session, `${fixture.origin}/risky-actions.html`, runtime.config, runtime.events, runtime.screenReader);
    for (const blocked of ["Delete Account", "Billing", "Pay now"]) {
      const element = [...session.currentElements.values()].find((candidate) => candidate.label === blocked);
      expect(element).toBeDefined();
      await expect(
        runtime.actionExecutor.execute(session, command(session.browserSessionId, "click_element", { element_id: element?.element_id })),
      ).rejects.toThrow();
    }
  });
});

function command(
  browserSessionId: string,
  actionType: BrowserActionCommand["action_type"],
  fields: Partial<BrowserActionCommand>,
): BrowserActionCommand {
  return {
    command_id: "00000000-0000-0000-0000-000000000030",
    session_id: "00000000-0000-0000-0000-000000000010",
    browser_session_id: browserSessionId,
    action_type: actionType,
    created_at: new Date().toISOString(),
    ...fields,
  };
}

