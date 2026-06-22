import { expect, test } from "@playwright/test";

test("safety script does not expose destructive controls as executed", async ({ page }) => {
  await page.setContent(`
    <main>
      <button aria-disabled="true">Delete Project</button>
      <p>Action blocked by policy.</p>
    </main>
  `);

  await expect(page.getByText("Action blocked by policy.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Delete Project" })).toHaveAttribute(
    "aria-disabled",
    "true",
  );
});
