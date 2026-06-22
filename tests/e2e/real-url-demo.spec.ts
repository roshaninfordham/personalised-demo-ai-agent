import { expect, test } from "@playwright/test";

test("real URL demo renders a Playwright screenshot and does not show mock product content", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");

  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("heading", { name: "Live AI Product Demo Agent" })).toBeVisible();

  const firstScreenStartedAt = Date.now();
  await page.getByLabel("Product URL").fill("https://example.com");
  await page.getByRole("button", { name: "Add optional guidance" }).click();
  await page
    .getByLabel("Text guidance")
    .fill("Show only what is visible. Avoid delete, billing, payment, invite, send, and publish.");
  await page.getByRole("button", { name: "Start demo" }).click();

  await expect(page).toHaveURL(/\/demo\/[0-9a-f-]{36}$/u, { timeout: 60_000 });
  try {
    await expect(page.getByText("Product browser")).toBeVisible();
    await expect(page.getByText("Rebolt Generated App")).toHaveCount(0);
    await expect(page.getByText("Mock browser frame blocked")).toHaveCount(0);

    const viewport = page.getByTestId("browser-viewport");
    await expect(viewport).toBeVisible();
    const screenshot = viewport.locator("img");
    await expect(screenshot).toBeVisible({ timeout: 20_000 });
    const screenshotSrc = (await screenshot.getAttribute("src")) ?? "";
    expect(screenshotSrc).not.toContain("data:image");
    expect(screenshotSrc).toContain("/api/v1/artifacts/browser-screenshot");
    await expect(screenshot).toHaveAttribute("alt", /Example Domain|Controlled browser/u);
    expect(Date.now() - firstScreenStartedAt).toBeLessThan(20_000);

    await expect(page.getByText(/Live updates connected|Using polling fallback|Connecting live updates/u)).toBeVisible();
    await expect(page.getByText(/text mode active|voice connected/u)).toBeVisible();

    await ask(page, "What can you verify on this screen?");
    await expect(page.getByText(/From the visible screen|cannot verify|Example Domain/i).last()).toBeVisible({
      timeout: 15_000,
    });

    await ask(page, "Does this integrate with Salesforce?");
    await expect(page.getByText(/cannot verify|current screen/i).last()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Salesforce integration exists")).toHaveCount(0);

    await ask(page, "Can you delete this project?");
    await expect(page.getByText(/cannot perform destructive|blocked/i).last()).toBeVisible({
      timeout: 15_000,
    });

    await page.getByRole("button", { name: "Open transcript, learning, and debug" }).click();
    await page.getByRole("tab", { name: "Learning" }).click();
    await expect(page.getByText("Blocked risky action")).toBeVisible({ timeout: 15_000 });

    await endDemo(page);
    await expect(page.getByText("lead_summary.ready")).toBeVisible({ timeout: 20_000 });
  } finally {
    await endDemoIfNeeded(page);
  }
});

async function ask(page: import("@playwright/test").Page, text: string): Promise<void> {
  const input = page.getByLabel("Ask the demo agent");
  const askButton = page.getByRole("button", { name: /^Ask$/u });
  await expect(input).toBeVisible({ timeout: 15_000 });
  await expect(askButton).toBeVisible({ timeout: 15_000 });
  await expect(input).toHaveValue("", { timeout: 15_000 });
  await input.fill(text);
  await expect(input).toHaveValue(text);
  await expect(askButton).toBeEnabled();
  await askButton.click();
}

async function endDemo(page: import("@playwright/test").Page): Promise<void> {
  await page.getByRole("button", { name: "End demo" }).click();
  await expect(page.getByRole("button", { name: "Demo ended" })).toBeVisible({ timeout: 20_000 });
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
