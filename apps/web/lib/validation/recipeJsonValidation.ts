export type RecipeJsonValidationResult = {
  valid: boolean;
  parsed?: Record<string, unknown>;
  errors: string[];
};

const blockedAllowedActions = new Set(["delete", "remove", "payment", "billing", "send", "publish", "invite"]);

export function validateRecipeJson(value: string): RecipeJsonValidationResult {
  if (value.trim() === "") return { valid: true, errors: [] };
  try {
    const parsed = JSON.parse(value) as unknown;
    if (!isRecord(parsed)) return { valid: false, errors: ["Recipe JSON must be an object."] };
    const steps = parsed.steps;
    if (!Array.isArray(steps)) return { valid: false, errors: ["Recipe JSON must include a steps array."] };
    const errors: string[] = [];
    if (steps.length === 0 || steps.length > 50) errors.push("Recipe steps must contain 1 to 50 items.");
    const seenOrders = new Set<number>();
    for (const [index, step] of steps.entries()) {
      if (!isRecord(step)) {
        errors.push(`steps[${String(index)}] must be an object.`);
        continue;
      }
      const order = step.step_order;
      if (typeof order !== "number" || !Number.isInteger(order)) {
        errors.push(`steps[${String(index)}].step_order must be an integer.`);
      } else if (seenOrders.has(order)) {
        errors.push(`Duplicate step_order ${String(order)}.`);
      } else {
        seenOrders.add(order);
      }
      const allowed = step.allowed_actions;
      if (Array.isArray(allowed)) {
        for (const action of allowed) {
          if (typeof action === "string" && blockedAllowedActions.has(action.toLowerCase())) {
            errors.push(`Blocked allowed action: ${action}.`);
          }
        }
      }
    }
    return { valid: errors.length === 0, parsed, errors };
  } catch {
    return { valid: false, errors: ["Recipe JSON is not valid JSON."] };
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
