import { describe, expect, it } from "vitest";

import { classifyElementRisk } from "../src/actions/riskClassifier.js";

function classify(label: string) {
  return classifyElementRisk({
    role: "button",
    label,
    tagName: "button",
    currentUrl: "https://example.com",
    surroundingText: label,
    recipeNeverClick: [],
    globalNeverClick: ["Billing"],
    allowedDomains: ["example.com"],
  });
}

describe("risk classifier", () => {
  it("blocks destructive and never-click actions", () => {
    expect(classify("Delete Account").riskLevel).toBe("blocked");
    expect(classify("Billing").riskLevel).toBe("blocked");
  });

  it("classifies high, medium, and low risk", () => {
    expect(classify("Export Data").riskLevel).toBe("high");
    expect(classify("Create Report").riskLevel).toBe("medium");
    expect(classify("View Dashboard").riskLevel).toBe("low");
  });

  it("blocks risky external domains", () => {
    const result = classifyElementRisk({
      role: "link",
      label: "Checkout",
      tagName: "a",
      href: "https://evil.example.net/pay",
      currentUrl: "https://example.com",
      surroundingText: "Checkout",
      recipeNeverClick: [],
      globalNeverClick: [],
      allowedDomains: ["example.com"],
    });
    expect(result.riskLevel).toBe("blocked");
  });

  it("blocks sensitive auth and secret fields before scoring", () => {
    const password = classifyElementRisk({
      role: "input",
      label: "Password",
      tagName: "input",
      inputType: "password",
      currentUrl: "https://example.com/signup",
      surroundingText: "Create an account Password",
      recipeNeverClick: [],
      globalNeverClick: [],
      allowedDomains: ["example.com"],
    });
    expect(password).toMatchObject({
      riskLevel: "blocked",
      riskScore: 1,
    });

    const apiKey = classifyElementRisk({
      role: "input",
      label: "API key",
      tagName: "input",
      inputType: "text",
      currentUrl: "https://example.com/settings",
      surroundingText: "API key",
      recipeNeverClick: [],
      globalNeverClick: [],
      allowedDomains: ["example.com"],
    });
    expect(apiKey.riskLevel).toBe("blocked");
  });
});
