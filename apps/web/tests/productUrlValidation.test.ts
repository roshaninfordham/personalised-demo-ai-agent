import { describe, expect, it } from "vitest";

import { validateProductUrl } from "../lib/validation/productUrlValidation";

describe("validateProductUrl", () => {
  it("accepts and normalizes https URLs", () => {
    const result = validateProductUrl("HTTPS://Example.COM/path#frag");
    expect(result.valid).toBe(true);
    expect(result.normalizedUrl).toBe("https://example.com/path");
  });

  it("rejects dangerous schemes", () => {
    expect(validateProductUrl("javascript:alert(1)").valid).toBe(false);
    expect(validateProductUrl("data:text/html,hi").valid).toBe(false);
    expect(validateProductUrl("file:///tmp/test").valid).toBe(false);
  });

  it("warns on localhost when local URLs are not allowed", () => {
    const result = validateProductUrl("http://localhost:3000");
    expect(result.valid).toBe(true);
    expect(result.warning).toContain("Local");
  });
});
