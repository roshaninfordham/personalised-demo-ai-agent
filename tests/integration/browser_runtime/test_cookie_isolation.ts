import { afterEach, beforeEach, describe, expect, it } from "vitest";

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

describe("browser context isolation", () => {
  it("does not leak cookies between sessions", async () => {
    const sessionA = await createTestSession(runtime, fixture.origin);
    const sessionB = await runtime.sessionManager.createSession({
      organizationId: "00000000-0000-0000-0000-000000000001",
      demoSessionId: "00000000-0000-0000-0000-000000000011",
      productId: "00000000-0000-0000-0000-000000000020",
      viewport: { width: 1280, height: 800 },
      allowedDomains: ["127.0.0.1"],
      startUrl: fixture.origin,
    });

    await sessionA.page.goto(fixture.origin);
    await sessionA.context.addCookies([{ name: "demo", value: "a", domain: "127.0.0.1", path: "/" }]);
    await sessionB.page.goto(fixture.origin);

    expect((await sessionB.context.cookies()).some((cookie) => cookie.name === "demo")).toBe(false);
  });
});

