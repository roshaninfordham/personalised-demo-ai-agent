import { expect, test } from "@playwright/test";

test("recovery copy is honest and avoids unsupported product failure claims", async ({ page }) => {
  await page.setContent(`
    <main>
      <section aria-label="Recovery">
        <p>I can’t verify that step from the current screen, so I’ll avoid clicking further.</p>
      </section>
    </main>
  `);

  await expect(page.getByText("avoid clicking further")).toBeVisible();
  await expect(page.getByText("The product is broken")).toHaveCount(0);
});
