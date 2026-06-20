import type { PlaywrightTestConfig } from "playwright/test";

const config: PlaywrightTestConfig = {
  testDir: "./tests",
  timeout: 30_000,
  use: {
    headless: true,
  },
};

export default config;

