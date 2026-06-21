import Ajv2020 from "ajv/dist/2020";
import { readFileSync, readdirSync } from "node:fs";
import { basename, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const RULE_DIR = join(ROOT, "rules");
const SCHEMA_DIR = join(ROOT, "schemas");

type JsonObject = Record<string, unknown>;

function readJson(path: string): JsonObject {
  const parsed: unknown = JSON.parse(readFileSync(path, "utf8"));
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error(`${path} must contain a JSON object`);
  }
  return parsed as JsonObject;
}

function checkObjectSchemas(value: unknown, path: string): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      checkObjectSchemas(item, `${path}[${String(index)}]`);
    });
    return;
  }
  if (typeof value !== "object" || value === null) return;
  const objectValue = value as JsonObject;
  if (objectValue.type === "object" && !Object.hasOwn(objectValue, "additionalProperties")) {
    throw new Error(`${path} has type object but does not define additionalProperties`);
  }
  Object.entries(objectValue).forEach(([key, child]) => {
    checkObjectSchemas(child, `${path}.${key}`);
  });
}

const schemaFiles = readdirSync(SCHEMA_DIR)
  .filter((name) => name.endsWith(".schema.json"))
  .sort();
const schemas = schemaFiles.map((schemaFile) => {
  const schema = readJson(join(SCHEMA_DIR, schemaFile));
  if (typeof schema.$id !== "string" || schema.$id.length === 0) {
    throw new Error(`${schemaFile} must define $id`);
  }
  checkObjectSchemas(schema, basename(schemaFile));
  return { schemaFile, schema };
});

const ajv = new Ajv2020({ allErrors: true, strict: false, validateFormats: false });
schemas.forEach(({ schema }) => ajv.addSchema(schema));

const ruleSchemaMap = new Map<string, string>([
  ["action_safety_rules.json", "https://schemas.live-demo-agent.local/action-policy.schema.json"],
  ["rbac_permissions.json", "https://schemas.live-demo-agent.local/rbac.schema.json"],
  ["redaction_rules.json", "https://schemas.live-demo-agent.local/redaction.schema.json"],
  ["audit_action_catalog.json", "https://schemas.live-demo-agent.local/audit.schema.json"],
]);

for (const ruleFile of readdirSync(RULE_DIR).filter((name) => name.endsWith(".json")).sort()) {
  const rule = readJson(join(RULE_DIR, ruleFile));
  const schemaId = ruleSchemaMap.get(ruleFile);
  if (schemaId === undefined) continue;
  const validate = ajv.getSchema(schemaId);
  if (validate === undefined) throw new Error(`Missing schema ${schemaId}`);
  if (!validate(rule)) {
    throw new Error(`${ruleFile} failed validation: ${JSON.stringify(validate.errors)}`);
  }
}

console.log(`Validated ${String(schemaFiles.length)} policy schemas and rules.`);
