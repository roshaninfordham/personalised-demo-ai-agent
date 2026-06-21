import { describe, expect, it } from "vitest";

import { validateRecipeJson } from "../lib/validation/recipeJsonValidation";

describe("validateRecipeJson", () => {
  it("allows empty recipe JSON", () => {
    expect(validateRecipeJson("").valid).toBe(true);
  });

  it("parses valid recipe JSON", () => {
    const result = validateRecipeJson('{"steps":[{"step_order":0,"step_key":"overview","goal":"Show overview"}]}');
    expect(result.valid).toBe(true);
    expect(result.parsed).toBeDefined();
  });

  it("rejects invalid JSON and blocked actions", () => {
    expect(validateRecipeJson("{").valid).toBe(false);
    const blocked = validateRecipeJson(
      '{"steps":[{"step_order":0,"step_key":"billing","goal":"Billing","allowed_actions":["billing"]}]}',
    );
    expect(blocked.valid).toBe(false);
  });
});
