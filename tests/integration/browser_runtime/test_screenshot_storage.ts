import { afterEach, beforeEach, describe, expect, it } from "vitest";

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

describe("screenshot storage", () => {
  it("stores screenshot artifacts without returning base64 payloads", async () => {
    const session = await createTestSession(runtime, fixture.origin);
    await navigateSession(session, `${fixture.origin}/simple-dashboard.html`, runtime.config, runtime.events, runtime.screenReader);

    const screen = await runtime.screenReader.readCurrentScreen(session, { captureScreenshot: true });

    expect(screen.screenshot_uri).toContain("/screenshots/");
    expect(JSON.stringify(screen)).not.toContain("base64");
  });
});

