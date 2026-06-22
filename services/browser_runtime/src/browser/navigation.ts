import { isIP } from "node:net";

import type { Page } from "playwright";

import type { BrowserRuntimeConfig } from "../config.js";
import { BrowserRuntimeError } from "../errors.js";
import type { BrowserEventPublisher } from "../events/browserEventPublisher.js";
import type { ScreenReader } from "../screen/screenReader.js";
import { waitForPageIdle } from "./waitStrategies.js";
import type { BrowserSessionRecord } from "./browserSession.js";

export type NavigationPolicy = {
  appEnv: string;
  allowLocalProductUrls: boolean;
  allowedDomains: string[];
  blockExternalNavigation: boolean;
  maxUrlLength: number;
};

export type NormalizedUrlResult =
  | { ok: true; url: string; hostname: string }
  | { ok: false; errorCode: string; message: string };

export function validateNavigationUrl(url: string, policy: NavigationPolicy): NormalizedUrlResult {
  if (url.length > policy.maxUrlLength) {
    return { ok: false, errorCode: "url_too_long", message: "URL is too long." };
  }
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return { ok: false, errorCode: "invalid_url", message: "URL is invalid." };
  }
  if (!["http:", "https:"].includes(parsed.protocol)) {
    return { ok: false, errorCode: "blocked_scheme", message: "URL scheme is not allowed." };
  }
  if (parsed.username || parsed.password) {
    return {
      ok: false,
      errorCode: "url_credentials_blocked",
      message: "URL credentials are not allowed.",
    };
  }
  if (parsed.hostname.trim() === "") {
    return { ok: false, errorCode: "missing_hostname", message: "URL hostname is required." };
  }
  parsed.protocol = parsed.protocol.toLowerCase();
  parsed.hostname = parsed.hostname.toLowerCase();
  parsed.hash = "";
  const hostname = parsed.hostname;
  if (isMetadataHost(hostname)) {
    return {
      ok: false,
      errorCode: "metadata_endpoint_blocked",
      message: "Cloud metadata endpoints are blocked.",
    };
  }
  if (isPrivateOrLocalHost(hostname) && !(policy.appEnv === "local" && policy.allowLocalProductUrls)) {
    return {
      ok: false,
      errorCode: "private_url_blocked",
      message: "Private or local URLs are blocked.",
    };
  }
  if (policy.blockExternalNavigation && policy.allowedDomains.length > 0) {
    const allowed = policy.allowedDomains.some((domain) => domainMatches(hostname, domain));
    if (!allowed) {
      return {
        ok: false,
        errorCode: "external_navigation_blocked",
        message: "URL hostname is not allowlisted.",
      };
    }
  }
  return { ok: true, url: parsed.toString(), hostname };
}

export async function navigateSession(
  session: BrowserSessionRecord,
  url: string,
  config: BrowserRuntimeConfig,
  events: BrowserEventPublisher,
  screenReader: ScreenReader,
): Promise<{ success: true; final_url: string; redirect_chain: string[]; latency_ms: number }> {
  const started = performance.now();
  const validation = validateNavigationUrl(url, {
    appEnv: config.appEnv,
    allowLocalProductUrls: config.allowLocalProductUrls,
    allowedDomains: session.allowedDomains,
    blockExternalNavigation: config.browserBlockExternalNavigation,
    maxUrlLength: 2048,
  });
  if (!validation.ok) {
    throw new BrowserRuntimeError(validation.errorCode, validation.message, 422);
  }
  await events.publish(session, "browser.navigation.started", { url: validation.url });
  session.status = "navigating";
  const redirectChain: string[] = [];
  const response = await session.page.goto(validation.url, {
    waitUntil: "domcontentloaded",
    timeout: config.browserNavigationTimeoutMs,
  });
  if (response !== null) {
    redirectChain.push(response.url());
  }
  await waitForPageIdle(session.page, config);
  const finalUrl = session.page.url();
  const finalValidation = validateNavigationUrl(finalUrl, {
    appEnv: config.appEnv,
    allowLocalProductUrls: config.allowLocalProductUrls,
    allowedDomains: session.allowedDomains,
    blockExternalNavigation: config.browserBlockExternalNavigation,
    maxUrlLength: 2048,
  });
  if (!finalValidation.ok) {
    throw new BrowserRuntimeError("redirect_blocked", "Redirect target was blocked.", 403);
  }
  session.status = "active";
  await screenReader.readCurrentScreen(session, { captureScreenshot: config.browserEnableScreenshots });
  await events.publish(session, "browser.navigation.completed", {
    final_url: finalUrl,
    status: response?.status() ?? null,
  });
  return {
    success: true,
    final_url: finalUrl,
    redirect_chain: [...redirectChain, finalUrl],
    latency_ms: Math.round(performance.now() - started),
  };
}

export async function goBack(page: Page, config: BrowserRuntimeConfig): Promise<void> {
  await page.goBack({ waitUntil: "domcontentloaded", timeout: config.browserNavigationTimeoutMs });
  await waitForPageIdle(page, config);
}

function domainMatches(hostname: string, domain: string): boolean {
  const normalized = domain.toLowerCase().replace(/\.$/u, "");
  if (normalized.startsWith("*.")) {
    const suffix = normalized.slice(2);
    return hostname.endsWith(`.${suffix}`);
  }
  return hostname === normalized || hostname.endsWith(`.${normalized}`);
}

function isPrivateOrLocalHost(hostname: string): boolean {
  if (hostname === "localhost") {
    return true;
  }
  const ipVersion = isIP(hostname);
  if (ipVersion === 4) {
    const [a = 0, b = 0] = hostname.split(".").map((item) => Number.parseInt(item, 10));
    return (
      a === 0 ||
      a === 10 ||
      a === 127 ||
      a === 169 && b === 254 ||
      a === 172 && b >= 16 && b <= 31 ||
      a === 192 && b === 168 ||
      a === 100 && b >= 64 && b <= 127
    );
  }
  if (ipVersion === 6) {
    const normalized = hostname.toLowerCase();
    return normalized === "::1" || normalized.startsWith("fc") || normalized.startsWith("fd") || normalized.startsWith("fe80");
  }
  return false;
}

function isMetadataHost(hostname: string): boolean {
  const normalized = hostname.toLowerCase().replace(/\.$/u, "");
  return (
    normalized === "169.254.169.254" ||
    normalized === "metadata.google.internal" ||
    normalized === "100.100.100.200"
  );
}
