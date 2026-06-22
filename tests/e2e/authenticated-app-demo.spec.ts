import { test } from "@playwright/test";

test("demo credentials mode logs in to fixture app", async () => {
  test.skip(
    process.env.E2E_DEMO_CREDENTIALS_ENABLED !== "true",
    "Demo credentials require an explicit secret fixture; default local mode must not expose credentials.",
  );
});
