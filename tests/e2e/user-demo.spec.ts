import { expect, test } from "@playwright/test";

test("real local user demo journey renders browser frame, answers turns, blocks danger, and ends", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");

  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("heading", { name: "Live AI Product Demo Agent" })).toBeVisible();
  await expect(page.getByLabel("Product URL")).toBeVisible();

  await page.getByRole("button", { name: "Toggle color theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "Toggle color theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

  const firstScreenStartedAt = Date.now();
  await page.getByLabel("Product URL").fill("https://example.com");
  await page.getByRole("button", { name: "Add optional guidance" }).click();
  await page.getByLabel("Target persona").fill("founder");
  await page
    .getByLabel("Text guidance")
    .fill("I am a founder. Show dashboard, metric creation, and reports. Avoid billing and delete.");
  await page.getByRole("button", { name: "Start demo" }).click();

  await expect(page).toHaveURL(/\/demo\/[0-9a-f-]{36}$/u, { timeout: 60_000 });
  await expect(page.getByText("Controlled browser")).toBeVisible();
  const viewport = page.getByTestId("browser-viewport");
  await expect(viewport).toBeVisible();
  await expect(viewport.locator("img")).toBeVisible({ timeout: 15_000 });
  expect(Date.now() - firstScreenStartedAt).toBeLessThan(15_000);

  await expect(page.getByText(/Events: (connected|connecting|reconnecting)/u)).toBeVisible();
  await expect(page.getByText(/voice connected|text mode active/u)).toBeVisible();
  await expect(page.getByLabel("Ask the demo agent")).toBeVisible();
  await expect(page.getByText(/Welcome|loaded the product|product screen|demo/i).first()).toBeVisible({
    timeout: 15_000,
  });

  await page.getByRole("tab", { name: "Learning" }).click();
  await expect(page.getByText("Loaded product URL")).toBeVisible();
  await expect(page.getByText("Found clickable actions")).toBeVisible();
  await page.getByRole("tab", { name: "Assistant" }).click();

  await ask(page, "Can you show me the dashboard?");
  await expect(page.getByText(/visible screen|orienting|dashboard/i).last()).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.locator(".highlight-box")).toBeVisible({ timeout: 15_000 });
  await expect(page.locator(".cursor-dot")).toBeVisible();
  await expect(page.locator(".ripple")).toBeVisible({ timeout: 15_000 });

  await ask(page, "How do I create a new metric?");
  await expect(page.getByText(/metric creation|Add Metric|matching control/i).last()).toBeVisible({
    timeout: 15_000,
  });

  await ask(page, "Does this integrate with Salesforce?");
  await expect(page.getByText(/cannot verify|can.?t verify|current screen/i).last()).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByText("Salesforce integration exists")).toHaveCount(0);

  await ask(page, "Can you delete this project?");
  await expect(page.getByText(/cannot perform destructive|blocked/i).last()).toBeVisible({
    timeout: 15_000,
  });

  await page.getByRole("tab", { name: "Learning" }).click();
  await expect(page.getByText("Blocked risky action")).toBeVisible({ timeout: 15_000 });

  await page.getByRole("button", { name: "End demo" }).click();
  await expect(page.getByRole("button", { name: "Demo ended" })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("lead_summary.ready")).toBeVisible({ timeout: 20_000 });

  await page.getByRole("link", { name: "Metrics" }).click();
  await expect(page.getByRole("heading", { name: "Metrics & Analytics" })).toBeVisible();
});

async function ask(page: import("@playwright/test").Page, text: string): Promise<void> {
  const input = page.getByLabel("Ask the demo agent");
  const askButton = page.getByRole("button", { name: /^Ask$/u });
  await expect(askButton).toBeVisible({ timeout: 15_000 });
  await expect(input).toHaveValue("", { timeout: 15_000 });
  await input.fill(text);
  await expect(input).toHaveValue(text);
  await expect(askButton).toBeEnabled();
  await askButton.click();
}
