import { expect, test } from "@playwright/test";

test("login-required app is handled honestly and can open sign-up path safely", async ({
  page,
}) => {
  test.setTimeout(120_000);
  await page.goto("/");

  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByLabel("Product URL").fill("http://web:3000/fixtures/login-product");
  await page.getByRole("button", { name: "Add optional guidance" }).click();
  await page
    .getByLabel("Text guidance")
    .fill("Explain the visible login flow. Do not enter or ask for credentials.");
  await page.getByRole("button", { name: "Start demo" }).click();

  await expect(page).toHaveURL(/\/demo\/[0-9a-f-]{36}$/u, { timeout: 60_000 });
  await expect(page.getByTestId("browser-viewport").locator("img")).toBeVisible({
    timeout: 25_000,
  });
  await expect(page.getByText("Login required to continue the in-app demo")).toBeVisible({
    timeout: 20_000,
  });
  await expect(page.getByText(/email, password|password, email/u)).toBeVisible();
  await expect(page.getByText(/will not ask for or store credentials/i)).toBeVisible();

  const highlightSeen = waitForVisible(page.locator(".highlight-box"), 12_000);
  const rippleSeen = waitForVisible(page.locator(".ripple"), 12_000);

  await ask(page, "Can you walk me through how to sign up?");
  await expect(page.getByText(/sign-in screen|sign-up path|without submitting/i).last()).toBeVisible({
    timeout: 20_000,
  });
  await expect(page.getByText(/fixtures\/login-product\/signup/u)).toBeVisible({
    timeout: 25_000,
  });
  await expect(page.locator(".cursor-dot")).toBeVisible();
  expect(await highlightSeen).toBe(true);
  expect(await rippleSeen).toBe(true);

  await expect(page.getByText(/inside the app|dashboard workflow behind login/i)).toHaveCount(0);
  await endDemo(page);
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

async function waitForVisible(
  locator: import("@playwright/test").Locator,
  timeout: number,
): Promise<boolean> {
  return locator.waitFor({ state: "visible", timeout }).then(
    () => true,
    () => false,
  );
}

async function endDemo(page: import("@playwright/test").Page): Promise<void> {
  await page.getByRole("button", { name: "End demo" }).click();
  await expect(page.getByRole("button", { name: "Demo ended" })).toBeVisible({ timeout: 20_000 });
}
