import { describe, expect, it } from "vitest";

import { bboxCenter, toPublicElement, type InternalElement } from "../src/screen/elementExtractor.js";

describe("element extractor helpers", () => {
  it("maps internal elements to public elements without selector authority", () => {
    const element: InternalElement = {
      element_id: "el_button_abc",
      role: "button",
      label: "Open Dashboard",
      bbox: { x: 10, y: 20, width: 100, height: 40 },
      visible: true,
      enabled: true,
      risk_level: "low",
      confidence: 0.9,
      tagName: "button",
      inputType: undefined,
      href: undefined,
      placeholder: undefined,
      ariaLabel: undefined,
      text: "Open Dashboard",
      surroundingText: "Open Dashboard",
      selectorHint: "[data-live-demo-agent-el-index=\"0\"]",
      elementFingerprint: "fingerprint",
    };

    const publicElement = toPublicElement(element);

    expect(publicElement).toEqual({
      element_id: "el_button_abc",
      role: "button",
      label: "Open Dashboard",
      bbox: { x: 10, y: 20, width: 100, height: 40 },
      visible: true,
      enabled: true,
      risk_level: "low",
      confidence: 0.9,
    });
    expect("selectorHint" in publicElement).toBe(false);
  });

  it("computes viewport-relative bbox centers deterministically", () => {
    expect(bboxCenter({ x: 10, y: 20, width: 100, height: 40 })).toEqual({ x: 60, y: 40 });
  });
});
