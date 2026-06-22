import { expect, test } from "@playwright/test";

test("text mode remains interactive when voice is not configured", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");

  await page.getByLabel("Product URL").fill("https://example.com");
  await page.getByRole("button", { name: "Start demo" }).click();
  await expect(page).toHaveURL(/\/demo\/[0-9a-f-]{36}$/u, { timeout: 60_000 });
  await expect(page.getByTestId("browser-viewport").locator("img")).toBeVisible({
    timeout: 25_000,
  });
  await expect(page.getByText(/text mode active|voice connected/u)).toBeVisible();

  await ask(page, "What can you verify on this screen?");
  await expect(page.getByText(/From the visible screen|Example Domain|cannot verify/i).last()).toBeVisible({
    timeout: 20_000,
  });
  await endDemo(page);
});

async function ask(page: import("@playwright/test").Page, text: string): Promise<void> {
  const input = page.getByLabel("Ask the demo agent");
  const askButton = page.getByRole("button", { name: /^Ask$/u });
  await expect(input).toBeVisible({ timeout: 15_000 });
  await input.fill(text);
  await expect(askButton).toBeEnabled();
  await askButton.click();
}

async function endDemo(page: import("@playwright/test").Page): Promise<void> {
  await page.getByRole("button", { name: "End demo" }).click();
  await expect(page.getByRole("button", { name: "Demo ended" })).toBeVisible({ timeout: 20_000 });
}
