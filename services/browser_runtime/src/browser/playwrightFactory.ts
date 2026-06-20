import { chromium, type Browser } from "playwright";

import type { BrowserRuntimeConfig } from "../config.js";

export class PlaywrightFactory {
  private browser: Browser | undefined;

  constructor(private readonly config: BrowserRuntimeConfig) {}

  async getBrowser(): Promise<Browser> {
    if (this.browser?.isConnected() === true) {
      return this.browser;
    }
    this.browser = await chromium.launch({
      headless: this.config.browserHeadless,
      timeout: this.config.browserTimeoutMs,
    });
    return this.browser;
  }

  async isLaunchable(): Promise<boolean> {
    const browser = await this.getBrowser();
    return browser.isConnected();
  }

  async close(): Promise<void> {
    if (this.browser !== undefined) {
      await this.browser.close();
      this.browser = undefined;
    }
  }
}

