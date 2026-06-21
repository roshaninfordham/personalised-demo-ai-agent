import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const forbiddenEnvNames = [
  ["AI", "TEXT", "API", "KEY"],
  ["OBJECT", "STORAGE", "SECRET", "KEY"],
  ["DATABASE", "URL"],
  ["REDIS", "URL"],
  ["JWT", "SECRET"],
  ["SESSION", "SECRET"],
].map((parts) => parts.join("_"));

describe("frontend security constraints", () => {
  it("does not reference backend secret env vars", () => {
    const files = [
      "lib/config/publicConfig.ts",
      "lib/api/apiClient.ts",
      "components/demo-start/DemoStartForm.tsx",
      "components/live-demo/LiveDemoShell.tsx",
    ];
    const content = files.map((file) => readFileSync(join(process.cwd(), file), "utf8")).join("\n");
    for (const name of forbiddenEnvNames) {
      expect(content.includes(name)).toBe(false);
    }
  });
});
