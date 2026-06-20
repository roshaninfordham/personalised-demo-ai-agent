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
});
