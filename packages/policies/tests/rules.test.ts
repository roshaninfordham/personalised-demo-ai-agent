import { describe, expect, it } from "vitest";

import {
  actionSafetyRules,
  auditActionCatalog,
  rbacPermissions,
  redactionRules,
  recipePolicyDefaults,
} from "../generated/typescript/src/index.js";

describe("generated policy package", () => {
  it("exports required rule sets", () => {
    expect(actionSafetyRules.categories.length).toBeGreaterThan(0);
    expect(Object.keys(rbacPermissions.roles)).toContain("agent_runtime");
    expect(redactionRules.patterns.length).toBeGreaterThan(0);
    expect(recipePolicyDefaults.default_never_click).toContain("Billing");
    expect(auditActionCatalog.high_impact_actions).toContain("crm.export.requested");
  });
});
