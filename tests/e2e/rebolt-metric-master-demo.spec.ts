import { expect, test } from "@playwright/test";

import { apiBaseUrl } from "./runtimeEnv";

const REBOLT_METRIC_MASTER_URL =
  process.env.REBOLT_METRIC_MASTER_URL ?? "https://metric-master-suite505.apps.rebolt.ai/";

test("Rebolt Metric Master is handled as a real auth-gated product demo", async ({ page, request }) => {
  test.setTimeout(120_000);
  await page.goto("/");

  await page.getByLabel("Product URL").fill(REBOLT_METRIC_MASTER_URL);
  await page.getByRole("button", { name: "Start demo" }).click();
  await expect(page).toHaveURL(/\/demo\/[0-9a-f-]{36}$/u, { timeout: 60_000 });
  const sessionId = page.url().split("/").at(-1);
  expect(sessionId).toMatch(/^[0-9a-f-]{36}$/u);

  try {
    await expect(page.getByTestId("browser-viewport").locator("img")).toBeVisible({
      timeout: 30_000,
    });
    await expect(page.getByText("Login required to continue the in-app demo")).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByText(/email, password|password, email/u)).toBeVisible();

    await ask(page, "Can you walk me through how to sign up?");
    await expect(page.getByText(/sign-in screen|sign-up path|without submitting/i).last()).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.locator(".cursor-dot")).toBeVisible();
    await expect(page.locator(".highlight-box")).toBeVisible({ timeout: 15_000 });
    await expect(page.locator(".ripple")).toBeVisible({ timeout: 15_000 });

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
  } finally {
    await endDemoIfNeeded(page);
  }
});

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
