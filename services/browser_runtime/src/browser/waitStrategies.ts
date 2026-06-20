import type { Page } from "playwright";

import type { BrowserRuntimeConfig } from "../config.js";

export async function waitForPageIdle(page: Page, config: BrowserRuntimeConfig): Promise<void> {
  await page.waitForLoadState("domcontentloaded", {
    timeout: config.browserIdleTimeoutMs,
  }).catch(() => undefined);
  await page.waitForLoadState("networkidle", {
    timeout: config.browserIdleTimeoutMs,
  }).catch(() => undefined);
  await page.locator("body").waitFor({
    state: "visible",
    timeout: config.browserIdleTimeoutMs,
  }).catch(() => undefined);
  if (config.browserPostNavigationSettleMs > 0) {
    await page.waitForTimeout(config.browserPostNavigationSettleMs);
  }
}

