import { describe, expect, it } from "vitest";

import { validateNavigationUrl } from "../src/browser/navigation.js";

const policy = {
  appEnv: "production",
  allowLocalProductUrls: false,
  allowedDomains: ["example.com"],
  blockExternalNavigation: true,
  maxUrlLength: 2048,
};

describe("validateNavigationUrl", () => {
  it("accepts and normalizes https URLs", () => {
    const result = validateNavigationUrl("HTTPS://Example.COM/path#fragment", policy);
    expect(result.ok).toBe(true);
    expect(result.ok ? result.url : "").toBe("https://example.com/path");
  });

  it("rejects dangerous schemes and credentials", () => {
    expect(validateNavigationUrl("javascript:alert(1)", policy).ok).toBe(false);
    expect(validateNavigationUrl("data:text/html,hi", policy).ok).toBe(false);
    expect(validateNavigationUrl("file:///tmp/x", policy).ok).toBe(false);
    expect(validateNavigationUrl("mailto:test@example.com", policy).ok).toBe(false);
    expect(validateNavigationUrl("https://user:pass@example.com", policy).ok).toBe(false);
  });

  it("rejects localhost unless local mode allows it", () => {
    expect(validateNavigationUrl("http://127.0.0.1:3000", policy).ok).toBe(false);
    expect(
      validateNavigationUrl("http://127.0.0.1:3000", {
        ...policy,
        appEnv: "local",
        allowLocalProductUrls: true,
        allowedDomains: [],
      }).ok,
    ).toBe(true);
  });

  it("blocks non-allowlisted external domains", () => {
    const result = validateNavigationUrl("https://evil.example.net", policy);
    expect(result.ok).toBe(false);
  });

  it("rejects cloud metadata endpoints even when explicitly allowlisted", () => {
    const result = validateNavigationUrl("http://169.254.169.254/latest/meta-data", {
      ...policy,
      allowedDomains: ["169.254.169.254"],
    });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.errorCode).toBe("metadata_endpoint_blocked");
    }
  });

  it("allows wildcard subdomains", () => {
    const result = validateNavigationUrl("https://app.example.com/dashboard", {
      ...policy,
      allowedDomains: ["*.example.com"],
    });
    expect(result.ok).toBe(true);
  });
});
