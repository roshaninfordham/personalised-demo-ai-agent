export type BrowserRuntimeConfig = {
  appEnv: string;
  logLevel: string;
  host: string;
  port: number;
  browserProvider: "local_playwright";
  browserHeadless: boolean;
  browserViewportWidth: number;
  browserViewportHeight: number;
  browserTimeoutMs: number;
  browserActionTimeoutMs: number;
  browserNavigationTimeoutMs: number;
  browserIdleTimeoutMs: number;
  browserPostNavigationSettleMs: number;
  browserSessionTtlSeconds: number;
  browserCleanupIntervalMs: number;
  browserMaxConcurrentSessions: number;
  browserEnableScreenshots: boolean;
  browserScreenshotFormat: "webp" | "png" | "jpeg";
  browserScreenshotQuality: number;
  browserAllowedDomains: string[];
  browserBlockExternalNavigation: boolean;
  browserCloseAfterSession: boolean;
  allowLocalProductUrls: boolean;
  allowFileUploads: boolean;
  allowDownloads: boolean;
  allowPaymentPages: boolean;
  allowExternalEmailActions: boolean;
  allowDestructiveActions: boolean;
  requireConfirmationForHighRisk: boolean;
  redisUrl: string;
  redisKeyPrefix: string;
  redisSessionTtlSeconds: number;
  redisEventStreamMaxLen: number;
  objectStorageEndpoint: string;
  objectStorageAccessKey: string;
  objectStorageSecretKey: string;
  objectStorageBucket: string;
  objectStorageRegion: string;
  objectStorageForcePathStyle: boolean;
  objectStoragePresignedUrlTtlSeconds: number;
  cursorEnableOverlay: boolean;
  cursorMoveMinDurationMs: number;
  cursorMoveMaxDurationMs: number;
  cursorEasing: string;
  cursorClickRippleEnabled: boolean;
  elementHighlightDurationMs: number;
  actionExecutionScoreThreshold: number;
  defaultNeverClick: string[];
  screenVisibleTextMaxChars: number;
  screenMaxElements: number;
  domSummaryMaxNodes: number;
  domSummaryMaxTextPerNode: number;
  domSummaryMaxArrayItems: number;
  accessibilityMaxNodes: number;
  accessibilityMaxDepth: number;
  stagehandEnabled: boolean;
  stagehandAllowHotPath: boolean;
  stagehandProviderModel: string;
  browserUseEnabled: boolean;
  browserUseAllowHotPath: boolean;
  browserChromiumNoSandbox: boolean;
};

const DEFAULT_NEVER_CLICK = [
  "Delete",
  "Remove",
  "Billing",
  "Invite",
  "Send",
  "Publish",
  "Upgrade",
  "Payment",
  "Account Settings",
];

export function getConfig(env: NodeJS.ProcessEnv = process.env): BrowserRuntimeConfig {
  const config: BrowserRuntimeConfig = {
    appEnv: readString(env.APP_ENV, "local"),
    logLevel: readString(env.LOG_LEVEL, "info"),
    host: readString(env.BROWSER_RUNTIME_HOST, "0.0.0.0"),
    port: readInteger(env.BROWSER_RUNTIME_PORT, 8200, 1, 65_535),
    browserProvider: "local_playwright",
    browserHeadless: readBoolean(env.BROWSER_HEADLESS, true),
    browserViewportWidth: readInteger(env.BROWSER_VIEWPORT_WIDTH, 1440, 800, 2560),
    browserViewportHeight: readInteger(env.BROWSER_VIEWPORT_HEIGHT, 900, 600, 1600),
    browserTimeoutMs: readInteger(env.BROWSER_TIMEOUT_MS, 15_000, 1_000, 120_000),
    browserActionTimeoutMs: readInteger(env.BROWSER_ACTION_TIMEOUT_MS, 5_000, 500, 60_000),
    browserNavigationTimeoutMs: readInteger(
      env.BROWSER_NAVIGATION_TIMEOUT_MS,
      15_000,
      1_000,
      120_000,
    ),
    browserIdleTimeoutMs: readInteger(env.BROWSER_IDLE_TIMEOUT_MS, 1_500, 100, 30_000),
    browserPostNavigationSettleMs: readInteger(
      env.BROWSER_POST_NAVIGATION_SETTLE_MS,
      300,
      0,
      5_000,
    ),
    browserSessionTtlSeconds: readInteger(env.BROWSER_SESSION_TTL_SECONDS, 3_600, 60, 86_400),
    browserCleanupIntervalMs: readInteger(
      env.BROWSER_CLEANUP_INTERVAL_MS,
      30_000,
      1_000,
      600_000,
    ),
    browserMaxConcurrentSessions: readInteger(env.BROWSER_MAX_CONCURRENT_SESSIONS, 3, 1, 100),
    browserEnableScreenshots: readBoolean(env.BROWSER_ENABLE_SCREENSHOTS, true),
    browserScreenshotFormat: readScreenshotFormat(env.BROWSER_SCREENSHOT_FORMAT),
    browserScreenshotQuality: readInteger(env.BROWSER_SCREENSHOT_QUALITY, 70, 1, 100),
    browserAllowedDomains: readCsv(env.BROWSER_ALLOWED_DOMAINS),
    browserBlockExternalNavigation: readBoolean(env.BROWSER_BLOCK_EXTERNAL_NAVIGATION, true),
    browserCloseAfterSession: readBoolean(env.BROWSER_CLOSE_AFTER_SESSION, true),
    allowLocalProductUrls: readBoolean(env.ALLOW_LOCAL_PRODUCT_URLS, false),
    allowFileUploads: readBoolean(env.ALLOW_FILE_UPLOADS, false),
    allowDownloads: readBoolean(env.ALLOW_DOWNLOADS, false),
    allowPaymentPages: readBoolean(env.ALLOW_PAYMENT_PAGES, false),
    allowExternalEmailActions: readBoolean(env.ALLOW_EXTERNAL_EMAIL_ACTIONS, false),
    allowDestructiveActions: readBoolean(env.ALLOW_DESTRUCTIVE_ACTIONS, false),
    requireConfirmationForHighRisk: readBoolean(env.REQUIRE_CONFIRMATION_FOR_HIGH_RISK, true),
    redisUrl: readString(env.REDIS_URL, "redis://redis:6379/0"),
    redisKeyPrefix: readString(env.REDIS_KEY_PREFIX, "live_demo"),
    redisSessionTtlSeconds: readInteger(env.REDIS_SESSION_TTL_SECONDS, 86_400, 60, 604_800),
    redisEventStreamMaxLen: readInteger(env.REDIS_EVENT_STREAM_MAXLEN, 10_000, 100, 1_000_000),
    objectStorageEndpoint: readString(env.OBJECT_STORAGE_ENDPOINT, "http://minio:9000"),
    objectStorageAccessKey: readString(env.OBJECT_STORAGE_ACCESS_KEY, "minioadmin"),
    objectStorageSecretKey: readString(env.OBJECT_STORAGE_SECRET_KEY, "minioadmin"),
    objectStorageBucket: readString(env.OBJECT_STORAGE_BUCKET, "demo-agent-artifacts"),
    objectStorageRegion: readString(env.OBJECT_STORAGE_REGION, "local"),
    objectStorageForcePathStyle: readBoolean(env.OBJECT_STORAGE_FORCE_PATH_STYLE, true),
    objectStoragePresignedUrlTtlSeconds: readInteger(
      env.OBJECT_STORAGE_PRESIGNED_URL_TTL_SECONDS,
      300,
      1,
      3_600,
    ),
    cursorEnableOverlay: readBoolean(env.CURSOR_ENABLE_OVERLAY, true),
    cursorMoveMinDurationMs: readInteger(env.CURSOR_MOVE_MIN_DURATION_MS, 250, 0, 5_000),
    cursorMoveMaxDurationMs: readInteger(env.CURSOR_MOVE_MAX_DURATION_MS, 700, 0, 10_000),
    cursorEasing: readString(env.CURSOR_EASING, "easeOutCubic"),
    cursorClickRippleEnabled: readBoolean(env.CURSOR_CLICK_RIPPLE_ENABLED, true),
    elementHighlightDurationMs: readInteger(env.ELEMENT_HIGHLIGHT_DURATION_MS, 1_200, 0, 10_000),
    actionExecutionScoreThreshold: readNumber(
      env.ACTION_EXECUTION_SCORE_THRESHOLD,
      0.72,
      0,
      1,
    ),
    defaultNeverClick: readCsv(env.DEFAULT_NEVER_CLICK, DEFAULT_NEVER_CLICK),
    screenVisibleTextMaxChars: readInteger(env.SCREEN_VISIBLE_TEXT_MAX_CHARS, 12_000, 100, 100_000),
    screenMaxElements: readInteger(env.SCREEN_MAX_ELEMENTS, 200, 1, 1_000),
    domSummaryMaxNodes: readInteger(env.DOM_SUMMARY_MAX_NODES, 300, 1, 2_000),
    domSummaryMaxTextPerNode: readInteger(env.DOM_SUMMARY_MAX_TEXT_PER_NODE, 200, 10, 2_000),
    domSummaryMaxArrayItems: readInteger(env.DOM_SUMMARY_MAX_ARRAY_ITEMS, 50, 1, 500),
    accessibilityMaxNodes: readInteger(env.ACCESSIBILITY_MAX_NODES, 300, 1, 2_000),
    accessibilityMaxDepth: readInteger(env.ACCESSIBILITY_MAX_DEPTH, 8, 1, 20),
    stagehandEnabled: readBoolean(env.STAGEHAND_ENABLED, false),
    stagehandAllowHotPath: readBoolean(env.STAGEHAND_ALLOW_HOT_PATH, false),
    stagehandProviderModel: readString(env.STAGEHAND_PROVIDER_MODEL, ""),
    browserUseEnabled: readBoolean(env.BROWSER_USE_ENABLED, false),
    browserUseAllowHotPath: readBoolean(env.BROWSER_USE_ALLOW_HOT_PATH, false),
    browserChromiumNoSandbox: readBoolean(env.BROWSER_CHROMIUM_NO_SANDBOX, false),
  };
  if (config.cursorMoveMinDurationMs > config.cursorMoveMaxDurationMs) {
    throw new Error("CURSOR_MOVE_MIN_DURATION_MS must be <= CURSOR_MOVE_MAX_DURATION_MS.");
  }
  validateProductionSafety(config);
  return config;
}

export function safeConfig(config: BrowserRuntimeConfig): Record<string, unknown> {
  return {
    ...config,
    objectStorageAccessKey: "***REDACTED***",
    objectStorageSecretKey: "***REDACTED***",
  };
}

function validateProductionSafety(config: BrowserRuntimeConfig): void {
  if (config.appEnv !== "production") {
    return;
  }
  const violations: string[] = [];
  if (config.browserChromiumNoSandbox) violations.push("BROWSER_CHROMIUM_NO_SANDBOX");
  if (config.allowLocalProductUrls) violations.push("ALLOW_LOCAL_PRODUCT_URLS");
  if (config.allowDestructiveActions) violations.push("ALLOW_DESTRUCTIVE_ACTIONS");
  if (config.allowDownloads) violations.push("ALLOW_DOWNLOADS");
  if (config.allowFileUploads) violations.push("ALLOW_FILE_UPLOADS");
  if (config.allowPaymentPages) violations.push("ALLOW_PAYMENT_PAGES");
  if (!config.browserBlockExternalNavigation) violations.push("BROWSER_BLOCK_EXTERNAL_NAVIGATION=false");
  if (violations.length > 0) {
    throw new Error(`Unsafe browser production configuration: ${violations.join(", ")}.`);
  }
}

function readString(value: string | undefined, fallback: string): string {
  return value === undefined || value.trim() === "" ? fallback : value;
}

function readCsv(value: string | undefined, fallback: string[] = []): string[] {
  if (value === undefined || value.trim() === "") {
    return fallback;
  }
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function readBoolean(value: string | undefined, fallback: boolean): boolean {
  if (value === undefined || value.trim() === "") {
    return fallback;
  }
  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
}

function readInteger(value: string | undefined, fallback: number, min: number, max: number): number {
  const parsed = value === undefined || value.trim() === "" ? fallback : Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    throw new Error(`Expected integer env value in range [${String(min)}, ${String(max)}].`);
  }
  return parsed;
}

function readNumber(value: string | undefined, fallback: number, min: number, max: number): number {
  const parsed = value === undefined || value.trim() === "" ? fallback : Number.parseFloat(value);
  if (!Number.isFinite(parsed) || parsed < min || parsed > max) {
    throw new Error(`Expected numeric env value in range [${String(min)}, ${String(max)}].`);
  }
  return parsed;
}

function readScreenshotFormat(value: string | undefined): "webp" | "png" | "jpeg" {
  if (value === "webp" || value === "png" || value === "jpeg") {
    return value;
  }
  return "webp";
}
