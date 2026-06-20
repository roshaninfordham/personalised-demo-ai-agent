import type { Page } from "playwright";

import type { BrowserRuntimeConfig } from "../config.js";
import type { BrowserEventPublisher } from "../events/browserEventPublisher.js";
import { installDownloadGuards } from "./downloadGuards.js";
import { installNetworkGuards } from "./networkGuards.js";
import type { BrowserSessionRecord } from "./browserSession.js";

export async function installPageGuards(
  page: Page,
  session: BrowserSessionRecord,
  config: BrowserRuntimeConfig,
  events: BrowserEventPublisher,
): Promise<void> {
  installDownloadGuards(page, session, config, events);
  await installNetworkGuards(page, session, config, events);
  page.on("dialog", async (dialog) => {
    await events.publish(session, "browser.policy.blocked", {
      reason: "dialog_auto_dismissed",
      message: dialog.message(),
    });
    await dialog.dismiss();
  });
  page.on("popup", async (popup) => {
    await events.publish(session, "browser.policy.blocked", {
      reason: "unexpected_popup_closed",
      url: popup.url(),
    });
    await popup.close();
  });
}

