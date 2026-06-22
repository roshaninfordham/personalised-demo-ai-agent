import type { Page } from "playwright";

import type { BrowserRuntimeConfig } from "../config.js";
import type { BrowserEventPublisher } from "../events/browserEventPublisher.js";
import { validateNavigationUrl } from "./navigation.js";
import type { BrowserSessionRecord } from "./browserSession.js";

const BLOCKED_RESOURCE_TYPES = new Set(["manifest", "eventsource", "websocket"]);
const PAYMENT_HOST_TOKENS = ["stripe", "paypal", "checkout", "billing", "payment"];

export async function installNetworkGuards(
  page: Page,
  session: BrowserSessionRecord,
  config: BrowserRuntimeConfig,
  events: BrowserEventPublisher,
): Promise<void> {
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = request.url();
    const resourceType = request.resourceType();
    const result = validateNavigationUrl(url, {
      appEnv: config.appEnv,
      allowLocalProductUrls: config.allowLocalProductUrls,
      allowedDomains: session.allowedDomains,
      blockExternalNavigation: config.browserBlockExternalNavigation,
      maxUrlLength: 2048,
    });
    if (!result.ok) {
      await publishBlockedRequest(events, session, url, resourceType, result.errorCode);
      await route.abort("blockedbyclient");
      return;
    }
    if (!config.allowPaymentPages && hostLooksLikePayment(result.hostname)) {
      await publishBlockedRequest(events, session, url, resourceType, "payment_host_blocked");
      await route.abort("blockedbyclient");
      return;
    }
    if (BLOCKED_RESOURCE_TYPES.has(resourceType)) {
      await publishBlockedRequest(events, session, url, resourceType, "resource_type_blocked");
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });
}

async function publishBlockedRequest(
  events: BrowserEventPublisher,
  session: BrowserSessionRecord,
  url: string,
  resourceType: string,
  reason: string,
): Promise<void> {
  await events.publish(session, "browser.network.request_blocked", {
    reason,
    resource_type: resourceType,
    target_host: safeHost(url),
  });
}

function safeHost(url: string): string | null {
  try {
    return new URL(url).hostname.toLowerCase();
  } catch {
    return null;
  }
}

function hostLooksLikePayment(hostname: string): boolean {
  const normalized = hostname.toLowerCase();
  return PAYMENT_HOST_TOKENS.some((token) => normalized.includes(token));
}
