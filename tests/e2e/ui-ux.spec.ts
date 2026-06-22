import { expect, test } from "@playwright/test";

test("homepage and observability navigation are polished and readable", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Live AI Product Demo Agent" })).toBeVisible();
  await expect(page.getByLabel("Product URL")).toBeVisible();
  await expect(page.getByRole("button", { name: "Start demo" })).toBeVisible();
  await expect(page.getByText("Demo readiness: Ready in fake-provider mode")).toBeVisible();
  await expect(page.getByRole("link", { name: "Metrics & Analytics" }).first()).toBeVisible();

  const heroBox = await page.locator(".hero-panel").boundingBox();
  expect(heroBox?.width ?? 0).toBeGreaterThan(700);

  await page.getByRole("link", { name: "Observability" }).first().click();
  await expect(page.getByRole("heading", { name: "Observability" })).toBeVisible();
  await expect(page.getByText("make up-observability")).toBeVisible();
  await expect(page.getByRole("link", { name: /Grafana/u })).toBeVisible();
  await expect(page.getByRole("link", { name: /Prometheus/u })).toBeVisible();
});
