import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { navigateSession } from "../src/browser/navigation.js";
import type { BrowserActionCommand } from "@live-demo-agent/contracts";
import { buildTestRuntime, createTestSession, startFixtureServer, type TestRuntime } from "./testHelpers.js";

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

describe("action executor integration", () => {
  it("clicks safe buttons, types safe inputs, blocks password fields, scrolls and goes back", async () => {
    const session = await createTestSession(runtime, fixture.origin);
    await navigateSession(
      session,
      `${fixture.origin}/simple-dashboard.html`,
      runtime.config,
      runtime.events,
      runtime.screenReader,
    );
    const addMetric = [...session.currentElements.values()].find((element) => element.label === "Add Metric");
    expect(addMetric).toBeDefined();
    const addMetricId = addMetric?.element_id;
    if (addMetricId === undefined) throw new Error("missing add metric element");
    const clickResult = await runtime.actionExecutor.execute(
      session,
      command(session.browserSessionId, "click_element", {
        element_id: addMetricId,
      }),
    );
    expect(clickResult.success).toBe(true);
    expect(await session.page.locator("#metricAdded").innerText()).toBe("Metric added");

    await navigateSession(
      session,
      `${fixture.origin}/form-page.html`,
      runtime.config,
      runtime.events,
      runtime.screenReader,
    );
    const displayName = [...session.currentElements.values()].find(
      (element) =>
        element.role === "input" &&
        (element.label === "Display name" || element.placeholder === "Weekly KPI demo"),
    );
    expect(displayName).toBeDefined();
    const displayNameId = displayName?.element_id;
    if (displayNameId === undefined) throw new Error("missing display name element");
    await runtime.actionExecutor.execute(
      session,
      command(session.browserSessionId, "type_into_element", {
        element_id: displayNameId,
        text: "Founder KPI demo",
      }),
    );
    expect(await session.page.locator("#displayName").inputValue()).toBe("Founder KPI demo");

    const password = [...session.currentElements.values()].find((element) => element.inputType === "password");
    expect(password).toBeDefined();
    const passwordId = password?.element_id;
    if (passwordId === undefined) throw new Error("missing password element");
    await expect(
      runtime.actionExecutor.execute(
        session,
        command(session.browserSessionId, "type_into_element", {
          element_id: passwordId,
          text: "secret",
        }),
      ),
    ).rejects.toThrow();

    const scrollResult = await runtime.actionExecutor.execute(
      session,
      command(session.browserSessionId, "scroll", { direction: "down" }),
    );
    expect(scrollResult.success).toBe(true);
    const backResult = await runtime.actionExecutor.execute(
      session,
      command(session.browserSessionId, "go_back", {}),
    );
    expect(backResult.success).toBe(true);
  });

  it("blocks delete buttons", async () => {
    const session = await createTestSession(runtime, fixture.origin);
    await navigateSession(
      session,
      `${fixture.origin}/risky-actions.html`,
      runtime.config,
      runtime.events,
      runtime.screenReader,
    );
    const deleteButton = [...session.currentElements.values()].find((element) =>
      element.label.includes("Delete"),
    );
    expect(deleteButton?.risk_level).toBe("blocked");
    const deleteButtonId = deleteButton?.element_id;
    if (deleteButtonId === undefined) throw new Error("missing delete button element");
    await expect(
      runtime.actionExecutor.execute(
        session,
        command(session.browserSessionId, "click_element", {
          element_id: deleteButtonId,
        }),
      ),
    ).rejects.toThrow();
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
