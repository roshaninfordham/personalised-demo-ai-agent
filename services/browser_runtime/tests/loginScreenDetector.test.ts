import { describe, expect, it } from "vitest";

import type { InternalElement } from "../src/screen/elementExtractor";
import { detectLoginScreen } from "../src/screen/loginScreenDetector";

describe("detectLoginScreen", () => {
  it("detects a sign-in screen with email, password, and sign-up actions", () => {
    const detection = detectLoginScreen({
      url: "https://app.example.com/login",
      title: "Rebolt Generated App",
      visibleText: "Email Password Sign In Sign up Forgot password",
      elements: [
        element({
          role: "input",
          label: "Email",
          bbox: { x: 20, y: 80, width: 240, height: 40 },
          inputType: "email",
        }),
        element({
          role: "input",
          label: "Password",
          bbox: { x: 20, y: 140, width: 240, height: 40 },
          inputType: "password",
        }),
        element({
          role: "button",
          label: "Sign In",
          text: "Sign In",
          bbox: { x: 20, y: 200, width: 240, height: 44 },
        }),
        element({
          role: "link",
          label: "Sign up",
          text: "Sign up",
          bbox: { x: 20, y: 260, width: 80, height: 24 },
          href: "/signup",
        }),
      ],
    });

    expect(detection.login_required).toBe(true);
    expect(detection.confidence).toBeGreaterThanOrEqual(0.8);
    expect(detection.detected_fields).toEqual(expect.arrayContaining(["email", "password"]));
    expect(detection.detected_actions).toEqual(expect.arrayContaining(["sign_in", "sign_up"]));
    expect(detection.safe_options).toEqual(
      expect.arrayContaining(["explain_screen", "user_takeover_login"])
    );
  });

  it("does not classify a normal dashboard as a login screen", () => {
    const detection = detectLoginScreen({
      url: "https://app.example.com/dashboard",
      title: "Dashboard",
      visibleText: "Revenue Metrics Reports Add Metric",
      elements: [
        element({
          role: "button",
          label: "Add Metric",
          text: "Add Metric",
          bbox: { x: 20, y: 80, width: 160, height: 40 },
        }),
      ],
    });

    expect(detection.login_required).toBe(false);
    expect(detection.detected_fields).not.toContain("password");
  });
});

function element(overrides: Partial<InternalElement>): InternalElement {
  return {
    element_id: "el",
    role: "button",
    label: "",
    tagName: "button",
    inputType: undefined,
    href: undefined,
    placeholder: undefined,
    ariaLabel: undefined,
    text: undefined,
    surroundingText: "",
    selectorHint: "[data-live-demo-agent-el-index=\"0\"]",
    elementFingerprint: "fp",
    bbox: { x: 0, y: 0, width: 10, height: 10 },
    visible: true,
    enabled: true,
    risk_level: "low",
    confidence: 1,
    ...overrides,
  };
}
