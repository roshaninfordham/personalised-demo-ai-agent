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

describe("navigation integration", () => {
  it("navigates to local fixtures and returns screen state", async () => {
    const session = await createTestSession(runtime, fixture.origin);
    const result = await navigateSession(
      session,
      `${fixture.origin}/simple-dashboard.html`,
      runtime.config,
      runtime.events,
      runtime.screenReader,
    );
    expect(result.success).toBe(true);
    expect(session.currentScreenState?.title).toBe("Dashboard");
  });

  it("blocks disallowed redirects", async () => {
    const session = await createTestSession(runtime, fixture.origin);
    await expect(
      navigateSession(
        session,
        `${fixture.origin}/redirect-external`,
        runtime.config,
        runtime.events,
        runtime.screenReader,
      ),
    ).rejects.toThrow();
  });
});

