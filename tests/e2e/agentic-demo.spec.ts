import { expect, test } from "@playwright/test";

test("agentic demo safety copy blocks destructive actions", async ({ page }) => {
  await page.setContent(`
    <main>
      <section aria-label="Agent answer">
        <p>I cannot delete this project. That action is blocked by policy.</p>
        <p>From what I can verify on screen, I can show safe dashboard and reporting workflows.</p>
      </section>
    </main>
  `);

  await expect(page.getByText("blocked by policy")).toBeVisible();
  await expect(page.getByText("From what I can verify on screen")).toBeVisible();
  await expect(page.getByText("I deleted this project")).toHaveCount(0);
});
