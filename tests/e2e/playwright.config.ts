import { defineConfig, devices } from "@playwright/test";

import { apiBaseUrl, webBaseUrl } from "./runtimeEnv";

const webPort = new URL(webBaseUrl).port || "3000";

export default defineConfig({
  testDir: ".",
  testMatch: ["*.spec.ts"],
  timeout: 30_000,
  expect: { timeout: 10_000 },
  outputDir: "../../.local/test-artifacts/e2e",
  reporter: [["list"], ["junit", { outputFile: "../../.local/test-results/e2e-results.xml" }]],
  use: {
    baseURL: webBaseUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: `pnpm --filter @live-demo-agent/web dev -- --port ${webPort}`,
    url: webBaseUrl,
    reuseExistingServer: true,
    timeout: 120_000,
    env: {
      NEXT_PUBLIC_ENABLE_DEBUG_PANEL: "true",
      NEXT_PUBLIC_ENABLE_WEBRTC_PLACEHOLDER: "true",
      NEXT_PUBLIC_API_BASE_URL: apiBaseUrl,
      NEXT_PUBLIC_EVENTS_BASE_URL: apiBaseUrl,
    },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
