import { describe, expect, it } from "vitest";

import { getConfig, safeConfig } from "../src/config.js";

describe("getConfig", () => {
  it("uses safe defaults", () => {
    const config = getConfig({});
    expect(config.port).toBe(8200);
    expect(config.browserMaxConcurrentSessions).toBe(3);
    expect(config.stagehandEnabled).toBe(false);
  });

  it("validates numeric ranges", () => {
    expect(() => getConfig({ BROWSER_RUNTIME_PORT: "70000" })).toThrow();
  });

  it("redacts secrets from safe config", () => {
    const config = getConfig({ OBJECT_STORAGE_SECRET_KEY: "secret" });
    expect(safeConfig(config).objectStorageSecretKey).toBe("***REDACTED***");
  });

  it("rejects unsafe production browser settings", () => {
    expect(() =>
      getConfig({
        APP_ENV: "production",
        BROWSER_CHROMIUM_NO_SANDBOX: "true",
      }),
    ).toThrow(/Unsafe browser production configuration/u);
    expect(() =>
      getConfig({
        APP_ENV: "production",
        ALLOW_LOCAL_PRODUCT_URLS: "true",
      }),
    ).toThrow(/ALLOW_LOCAL_PRODUCT_URLS/u);
    expect(() =>
      getConfig({
        APP_ENV: "production",
        BROWSER_BLOCK_EXTERNAL_NAVIGATION: "false",
      }),
    ).toThrow(/BROWSER_BLOCK_EXTERNAL_NAVIGATION/u);
  });
});
