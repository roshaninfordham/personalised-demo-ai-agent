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

describe("browser recovery", () => {
  it("refreshes safe actions after a stale element failure", async () => {
    const session = await createTestSession(runtime, fixture.origin);
    await navigateSession(session, `${fixture.origin}/simple-dashboard.html`, runtime.config, runtime.events, runtime.screenReader);
    await runtime.screenReader.readCurrentScreen(session, { captureScreenshot: false });
    const metric = [...session.currentElements.values()].find((element) => element.label === "Add Metric");
    expect(metric).toBeDefined();

    await session.page.setContent("<main><h1>Dashboard</h1><button>Reports</button></main>");
    await expect(
      runtime.actionExecutor.execute(
        session,
        command(session.browserSessionId, "click_element", { element_id: metric?.element_id }),
      ),
    ).rejects.toThrow();

    const refreshed = await runtime.screenReader.readCurrentScreen(session, { captureScreenshot: false });
    expect(refreshed.elements.some((element) => element.label === "Reports")).toBe(true);
  });
});

function command(
  browserSessionId: string,
  actionType: BrowserActionCommand["action_type"],
  fields: Partial<BrowserActionCommand>,
): BrowserActionCommand {
  return {
    command_id: "00000000-0000-0000-0000-000000000031",
    session_id: "00000000-0000-0000-0000-000000000010",
    browser_session_id: browserSessionId,
    action_type: actionType,
    created_at: new Date().toISOString(),
    ...fields,
  };
}
