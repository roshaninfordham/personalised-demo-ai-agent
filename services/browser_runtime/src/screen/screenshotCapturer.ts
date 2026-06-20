import { createHash, randomUUID } from "node:crypto";

import type { Page } from "playwright";
import sharp from "sharp";

import type { BrowserRuntimeConfig } from "../config.js";
import type { ArtifactStore, StoredArtifact } from "../storage/artifactStore.js";
import { screenshotObjectKey } from "../storage/objectKeys.js";
import type { BrowserSessionRecord } from "../browser/browserSession.js";

export async function captureAndStoreScreenshot(
  page: Page,
  session: BrowserSessionRecord,
  screenId: string,
  config: BrowserRuntimeConfig,
  artifactStore: ArtifactStore,
): Promise<StoredArtifact | undefined> {
  if (!config.browserEnableScreenshots) {
    return undefined;
  }
  const screenshotType = config.browserScreenshotFormat === "png" ? "png" : "jpeg";
  const screenshotOptions = {
    type: screenshotType,
    fullPage: false,
    ...(screenshotType === "png" || config.browserScreenshotFormat === "webp"
      ? {}
      : { quality: config.browserScreenshotQuality }),
  } as const;
  const rawBytes = await page.screenshot(screenshotOptions);
  const bytes =
    config.browserScreenshotFormat === "webp"
      ? await sharp(rawBytes).webp({ quality: config.browserScreenshotQuality }).toBuffer()
      : rawBytes;
  const sha256Hex = createHash("sha256").update(bytes).digest("hex");
  const contentType =
    config.browserScreenshotFormat === "webp" ? "image/webp" : `image/${screenshotType}`;
  return artifactStore.putObject({
    artifactId: randomUUID(),
    objectKey: screenshotObjectKey({
      organizationId: session.organizationId,
      demoSessionId: session.demoSessionId,
      browserSessionId: session.browserSessionId,
      screenId,
      extension: config.browserScreenshotFormat,
    }),
    content: bytes,
    contentType,
    metadata: {
      sha256_hex: sha256Hex,
      organization_id: session.organizationId,
      demo_session_id: session.demoSessionId,
      browser_session_id: session.browserSessionId,
      screen_id: screenId,
    },
  });
}
