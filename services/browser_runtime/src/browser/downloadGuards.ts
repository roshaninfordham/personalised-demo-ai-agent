import type { Page } from "playwright";

import type { BrowserRuntimeConfig } from "../config.js";
import type { BrowserEventPublisher } from "../events/browserEventPublisher.js";
import type { BrowserSessionRecord } from "./browserSession.js";

export function installDownloadGuards(
  page: Page,
  session: BrowserSessionRecord,
  config: BrowserRuntimeConfig,
  events: BrowserEventPublisher,
): void {
  page.on("download", async (download) => {
    await events.publish(session, "browser.policy.blocked", {
      reason: "download_blocked",
      suggested_filename: download.suggestedFilename(),
    });
    if (!config.allowDownloads) {
      await download.cancel();
    }
  });
  page.on("filechooser", async (chooser) => {
    void chooser;
    await events.publish(session, "browser.policy.blocked", {
      reason: "file_upload_blocked",
    });
    if (!config.allowFileUploads) {
      await events.publish(session, "browser.policy.blocked", {
        reason: "file_chooser_not_accepted",
      });
    }
  });
}
