import { describe, expect, it } from "vitest";

import { getHealth } from "../src/health.js";

describe("getHealth", () => {
  it("returns ok status", () => {
    expect(getHealth().status).toBe("ok");
  });
});
