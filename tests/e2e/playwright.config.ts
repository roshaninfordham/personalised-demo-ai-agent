import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: ["*.spec.ts"],
  timeout: 30_000,
  expect: { timeout: 10_000 },
  outputDir: "../../.local/test-artifacts/e2e",
  reporter: [["list"], ["junit", { outputFile: "../../.local/test-results/e2e-results.xml" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: "pnpm --filter @live-demo-agent/web dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 120_000,
    env: {
      NEXT_PUBLIC_ENABLE_DEBUG_PANEL: "true",
      NEXT_PUBLIC_ENABLE_WEBRTC_PLACEHOLDER: "true",
    },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
