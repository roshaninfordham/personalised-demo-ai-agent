import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { generateSafeActions } from "../../../services/browser_runtime/src/actions/actionRanker.js";
import { navigateSession } from "../../../services/browser_runtime/src/browser/navigation.js";
import {
  buildTestRuntime,
  createTestSession,
  startFixtureServer,
  type TestRuntime,
} from "../../../services/browser_runtime/tests/testHelpers.js";

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

describe("screen extraction", () => {
  it("extracts visible text, elements, safe actions, and stable hashes", async () => {
    const session = await createTestSession(runtime, fixture.origin);
    await navigateSession(
      session,
      `${fixture.origin}/simple-dashboard.html`,
      runtime.config,
      runtime.events,
      runtime.screenReader,
    );

    const first = await runtime.screenReader.readCurrentScreen(session, {
      captureScreenshot: true,
    });
    const second = await runtime.screenReader.readCurrentScreen(session, {
      captureScreenshot: true,
    });

    expect(first.title).toBe("Dashboard");
    expect(first.visible_text.join(" ")).toContain("Revenue");
    expect(first.elements.some((element) => element.label === "Add Metric")).toBe(true);
    expect(first.elements.some((element) => element.label === "Reports")).toBe(true);
    expect(generateSafeActions(first.elements, first.screen_hash, 0).length).toBeGreaterThan(0);
    expect(first.screen_hash).toBe(second.screen_hash);
  });
});
