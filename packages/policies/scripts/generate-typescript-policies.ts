import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const RULE_DIR = join(ROOT, "rules");
const OUT_DIR = join(ROOT, "generated", "typescript", "src");
const HEADER = "// Generated from packages/policies/rules. Do not edit manually.\n\n";

const MODULES = new Map<string, string>([
  ["action_safety_rules.json", "actionSafetyRules.ts"],
  ["rbac_permissions.json", "rbacPermissions.ts"],
  ["redaction_rules.json", "redactionRules.ts"],
  ["recipe_policy_defaults.json", "recipePolicyDefaults.ts"],
  ["audit_action_catalog.json", "auditActionCatalog.ts"],
]);

function constantName(fileName: string): string {
  return basename(fileName, ".json")
    .split("_")
    .map((part, index) =>
      index === 0 ? part : `${part[0]?.toUpperCase() ?? ""}${part.slice(1)}`,
    )
    .join("");
}

mkdirSync(OUT_DIR, { recursive: true });
const exports: string[] = [];
for (const [ruleFile, moduleFile] of MODULES.entries()) {
  const data: unknown = JSON.parse(readFileSync(join(RULE_DIR, ruleFile), "utf8"));
  const name = constantName(ruleFile);
  exports.push(moduleFile);
  writeFileSync(
    join(OUT_DIR, moduleFile),
    `${HEADER}export const ${name} = ${JSON.stringify(data, null, 2)} as const;\n`,
  );
  writeFileSync(
    join(OUT_DIR, moduleFile.replace(/\.ts$/, ".js")),
    `${HEADER}export const ${name} = ${JSON.stringify(data, null, 2)};\n`,
  );
}

writeFileSync(
  join(OUT_DIR, "types.ts"),
  `${HEADER}export type PolicyDecisionValue = "allowed" | "blocked" | "confirmation_required" | "not_applicable";\nexport type RiskLevel = "low" | "medium" | "high" | "blocked" | "unknown";\n`,
);
writeFileSync(join(OUT_DIR, "types.js"), `${HEADER}export {};\n`);
writeFileSync(
  join(OUT_DIR, "index.ts"),
  `${HEADER}${exports
    .map((fileName) => `export * from "./${basename(fileName, ".ts")}.js";`)
    .join("\n")}\nexport * from "./types.js";\n`,
);
writeFileSync(
  join(OUT_DIR, "index.js"),
  `${HEADER}${exports
    .map((fileName) => `export * from "./${basename(fileName, ".ts")}.js";`)
    .join("\n")}\n`,
);
console.log(`Generated TypeScript policies in ${OUT_DIR}`);
