import type { Page } from "playwright";

import type { BrowserRuntimeConfig } from "../config.js";
import type { BrowserEventPublisher } from "../events/browserEventPublisher.js";
import { validateNavigationUrl } from "./navigation.js";
import type { BrowserSessionRecord } from "./browserSession.js";

export async function installNetworkGuards(
  page: Page,
  session: BrowserSessionRecord,
  config: BrowserRuntimeConfig,
  events: BrowserEventPublisher,
): Promise<void> {
  await page.route("**/*", async (route) => {
    const request = route.request();
    if (request.isNavigationRequest() && request.frame() === page.mainFrame()) {
      const result = validateNavigationUrl(request.url(), {
        appEnv: config.appEnv,
        allowLocalProductUrls: config.allowLocalProductUrls,
        allowedDomains: session.allowedDomains,
        blockExternalNavigation: config.browserBlockExternalNavigation,
        maxUrlLength: 2048,
      });
      if (!result.ok) {
        await events.publish(session, "browser.policy.blocked", {
          reason: result.errorCode,
          url: request.url(),
        });
        await route.abort("blockedbyclient");
        return;
      }
    }
    await route.continue();
  });
}

