import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { navigateSession } from "../src/browser/navigation.js";
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

describe("screen reader integration", () => {
  it("extracts title text elements bboxes and screenshot artifact metadata", async () => {
    const session = await createTestSession(runtime, fixture.origin);
    await navigateSession(
      session,
      `${fixture.origin}/simple-dashboard.html`,
      runtime.config,
      runtime.events,
      runtime.screenReader,
    );
    const screen = await runtime.screenReader.readCurrentScreen(session, { captureScreenshot: true });
    expect(screen.title).toBe("Dashboard");
    expect(screen.visible_text.join(" ")).toContain("Revenue");
    expect(screen.elements.some((element) => element.label === "Add Metric")).toBe(true);
    expect(screen.elements.every((element) => element.bbox.width >= 0)).toBe(true);
    expect(screen.screenshot_uri).toContain("/screenshots/");
  });
});

