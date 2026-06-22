import { afterEach, beforeEach, describe, expect, it } from "vitest";

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

describe("browser session lifecycle", () => {
  it("creates ready sessions and closes them idempotently", async () => {
    const session = await createTestSession(runtime, fixture.origin);

    expect(session.browserSessionId).toBeTruthy();
    expect(session.status).toBe("ready");

    await runtime.sessionManager.closeSession(session.browserSessionId);
    await runtime.sessionManager.closeSession(session.browserSessionId);
    expect(runtime.sessionManager.activeCount()).toBe(0);
  });
});
