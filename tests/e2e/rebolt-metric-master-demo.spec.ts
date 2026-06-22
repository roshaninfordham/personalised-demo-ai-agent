import { expect, test } from "@playwright/test";

import { apiBaseUrl } from "./runtimeEnv";

const REBOLT_METRIC_MASTER_URL =
  process.env.REBOLT_METRIC_MASTER_URL ?? "https://metric-master-suite505.apps.rebolt.ai/";

test("Rebolt Metric Master is handled as a real auth-gated product demo", async ({ page, request }) => {
  test.setTimeout(120_000);
  log("opening homepage");
  await page.goto("/");

  log(`starting demo for ${REBOLT_METRIC_MASTER_URL}`);
  await page.getByLabel("Product URL").fill(REBOLT_METRIC_MASTER_URL);
  await page.getByRole("button", { name: "Start demo" }).click();
  log("waiting for demo room URL");
  await expect(page).toHaveURL(/\/demo\/[0-9a-f-]{36}$/u, { timeout: 60_000 });
  const sessionId = page.url().split("/").at(-1);
  expect(sessionId).toMatch(/^[0-9a-f-]{36}$/u);
  log(`session created: ${String(sessionId)}`);

  try {
    await waitForBrowserFrame(page, request, String(sessionId));
    log("real browser frame is visible");
    await expect(page.getByText("Login required to continue the in-app demo")).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByText(/email, password|password, email/u)).toBeVisible();
    log("login-required state detected");

    await ask(page, "Can you walk me through how to sign up?");
    log("asked sign-up question");
    await expect(page.getByText(/sign-in screen|sign-up path|without submitting/i).last()).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.locator(".cursor-dot")).toBeVisible();
    await expect(page.locator(".highlight-box")).toBeVisible({ timeout: 15_000 });
    await expect(page.locator(".ripple")).toBeVisible({ timeout: 15_000 });
    log("cursor, highlight, and click ripple observed");

    const state = await request.get(`${apiBaseUrl}/api/v1/demo-sessions/${String(sessionId)}/state`);
    expect(state.ok()).toBe(true);
    const body = (await state.json()) as {
      live_state?: {
        current_screen?: {
          summary?: string;
          auth_state?: { login_required?: boolean };
        };
        safe_actions?: Array<{ label?: string; action_type?: string; risk_level?: string }>;
      };
    };
    expect(body.live_state?.current_screen?.summary ?? "").toMatch(/Create an account|Sign up|Welcome back/u);
    expect(body.live_state?.current_screen?.auth_state?.login_required).toBe(true);
    expect(body.live_state?.safe_actions ?? []).not.toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          action_type: "type_into_element",
          label: expect.stringMatching(/password|api key|token/iu),
          risk_level: expect.not.stringMatching(/^blocked$/u),
        }),
      ]),
    );
    log("backend state verified");
  } finally {
    await endDemoIfNeeded(page);
    log("demo cleanup requested");
  }
});

function log(message: string): void {
  process.stdout.write(`[rebolt-demo] ${message}\n`);
}

async function waitForBrowserFrame(
  page: import("@playwright/test").Page,
  request: import("@playwright/test").APIRequestContext,
  sessionId: string,
): Promise<void> {
  const image = page.getByTestId("browser-viewport").locator("img");
  const deadline = Date.now() + 35_000;
  let lastState: unknown = null;
  let lastLog = 0;

  while (Date.now() < deadline) {
    if (await image.isVisible().catch(() => false)) return;

    const response = await request.get(`${apiBaseUrl}/api/v1/demo-sessions/${sessionId}/state`).catch(
      () => null,
    );
    if (response?.ok()) {
      lastState = await response.json();
      const summary = summarizeState(lastState);
      if (Date.now() - lastLog > 3_000) {
        log(`waiting for browser frame: ${summary}`);
        lastLog = Date.now();
      }
      const serialized = JSON.stringify(lastState);
      if (
        serialized.includes("browser_session_limit_reached") ||
        serialized.includes("Browser session limit reached")
      ) {
        throw new Error(`Browser runtime is at capacity before frame capture. Last state: ${summary}`);
      }
    }

    await page.waitForTimeout(500);
  }

  throw new Error(
    `Browser frame did not appear for Rebolt demo. Last state: ${JSON.stringify(
      compactState(lastState),
      null,
      2,
    )}`,
  );
}

function summarizeState(state: unknown): string {
  const compact = compactState(state) as Record<string, unknown>;
  return [
    `session=${compact.session_status ?? "unknown"}`,
    `runtime=${compact.runtime_state ?? "unknown"}`,
    `browser=${compact.browser_status ?? "unknown"}`,
    `screen=${compact.has_screen ? "yes" : "no"}`,
    `diagnostics=${JSON.stringify(compact.diagnostics ?? [])}`,
  ].join(" ");
}

function compactState(state: unknown): unknown {
  if (state === null || typeof state !== "object") return state;
  const payload = state as {
    session?: { status?: string; runtime_state?: string };
    browser?: { status?: string; browser_session_id?: string | null; current_screen?: unknown };
    live_state?: { current_screen?: unknown };
    diagnostics?: unknown;
  };
  return {
    session_status: payload.session?.status,
    runtime_state: payload.session?.runtime_state,
    browser_status: payload.browser?.status,
    browser_session_id: payload.browser?.browser_session_id,
    has_screen: Boolean(payload.browser?.current_screen ?? payload.live_state?.current_screen),
    diagnostics: payload.diagnostics,
  };
}

async function ask(page: import("@playwright/test").Page, text: string): Promise<void> {
  const input = page.getByLabel("Ask the demo agent");
  const askButton = page.getByRole("button", { name: /^Ask$/u });
  await expect(input).toBeVisible({ timeout: 15_000 });
  await expect(input).toHaveValue("", { timeout: 15_000 });
  await input.fill(text);
  await expect(askButton).toBeEnabled();
  await askButton.click();
}

async function endDemoIfNeeded(page: import("@playwright/test").Page): Promise<void> {
  const endButton = page.getByRole("button", { name: "End demo" });
  if ((await endButton.count()) === 0) return;
  if (!(await endButton.isEnabled().catch(() => false))) return;
  await endButton.click().catch(() => undefined);
  await page.getByRole("button", { name: "Demo ended" }).waitFor({ state: "visible", timeout: 10_000 }).catch(
    () => undefined,
  );
}
