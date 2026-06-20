import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";
import { fileURLToPath } from "node:url";

const CONTRACTS_ROOT = fileURLToPath(new URL("..", import.meta.url));
const SCHEMA_DIR = join(CONTRACTS_ROOT, "schemas");
const OUT_DIR = join(CONTRACTS_ROOT, "generated", "typescript", "src");
const HEADER = "// Generated from packages/contracts/schemas. Do not edit manually.\n\n";

const FILE_NAME_MAP = new Map<string, string>([
  ["browser-action.schema.json", "browserAction.ts"],
  ["common.schema.json", "common.ts"],
  ["demo-recipe.schema.json", "demoRecipe.ts"],
  ["demo-session.schema.json", "demoSession.ts"],
  ["event.schema.json", "event.ts"],
  ["lead-summary.schema.json", "leadSummary.ts"],
  ["screen-state.schema.json", "screenState.ts"],
  ["transcript.schema.json", "transcript.ts"],
]);

const COMMON_TYPES = [
  "BoundingBox",
  "DemoPhase",
  "IsoDateTimeString",
  "JsonValue",
  "Metadata",
  "PolicyDecision",
  "ProviderName",
  "RiskLevel",
  "SessionStatus",
  "TraceId",
  "UuidString",
];

type JsonObject = Record<string, unknown>;

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readJson(path: string): JsonObject {
  const parsed: unknown = JSON.parse(readFileSync(path, "utf8"));

  if (!isObject(parsed)) {
    throw new Error(`${path} must contain a JSON object`);
  }

  return parsed;
}

function asObject(value: unknown, context: string): JsonObject {
  if (!isObject(value)) {
    throw new Error(`${context} must be an object`);
  }
  return value;
}

function refName(ref: string): string {
  const parts = ref.split("/");
  const lastPart = parts.at(-1);

  if (lastPart === undefined || lastPart.length === 0) {
    throw new Error(`Invalid $ref: ${ref}`);
  }

  return lastPart;
}

function literal(value: unknown): string {
  if (typeof value !== "string") {
    throw new Error("Enum values must be strings");
  }
  return JSON.stringify(value);
}

function schemaType(schema: JsonObject): string {
  const ref = schema.$ref;
  if (typeof ref === "string") {
    return refName(ref);
  }

  const oneOf = schema.oneOf;
  if (Array.isArray(oneOf)) {
    return oneOf.map((item) => schemaType(asObject(item, "oneOf item"))).join(" | ");
  }

  if (Array.isArray(schema.enum)) {
    return schema.enum.map(literal).join(" | ");
  }

  if (schema.type === "string") {
    return "string";
  }
  if (schema.type === "integer" || schema.type === "number") {
    return "number";
  }
  if (schema.type === "boolean") {
    return "boolean";
  }
  if (schema.type === "null") {
    return "null";
  }
  if (schema.type === "array") {
    const items = asObject(schema.items, "array items");
    const itemType = schemaType(items);
    return itemType.includes(" | ") ? `(${itemType})[]` : `${itemType}[]`;
  }
  if (schema.type === "object") {
    const additionalProperties = schema.additionalProperties;
    if (isObject(additionalProperties)) {
      return `Record<string, ${schemaType(additionalProperties)}>`;
    }
    return "Record<string, never>";
  }

  throw new Error(`Unsupported schema type: ${JSON.stringify(schema)}`);
}

function renderType(name: string, schema: JsonObject): string {
  if (name === "JsonValue") {
    return [
      "export interface JsonObject {",
      "  [key: string]: JsonValue;",
      "}",
      "",
      "export type JsonValue = string | number | boolean | null | JsonValue[] | JsonObject;",
      "",
    ].join("\n");
  }
  if (name === "Metadata") {
    return "export type Metadata = JsonObject;\n";
  }

  if (Array.isArray(schema.enum)) {
    return `export type ${name} = ${schema.enum.map(literal).join(" | ")};\n`;
  }

  if (schema.type !== "object" || !isObject(schema.properties)) {
    return `export type ${name} = ${schemaType(schema)};\n`;
  }

  const required = new Set(Array.isArray(schema.required) ? schema.required : []);
  const lines = [`export interface ${name} {`];

  Object.entries(schema.properties).forEach(([propertyName, propertySchema]) => {
    const optional = required.has(propertyName) ? "" : "?";
    lines.push(
      `  ${propertyName}${optional}: ${schemaType(asObject(propertySchema, propertyName))};`,
    );
  });

  lines.push("}\n");
  return lines.join("\n");
}

function renderFile(schemaFileName: string, schema: JsonObject): string {
  const defs = asObject(schema.$defs, `${schemaFileName} $defs`);
  const imports =
    schemaFileName === "common.schema.json"
      ? ""
      : `import type { ${COMMON_TYPES.join(", ")} } from "./common";\n\n`;
  const body = Object.entries(defs)
    .map(([name, definition]) => renderType(name, asObject(definition, name)))
    .join("\n");

  return `${HEADER}${imports}${body}`;
}

mkdirSync(OUT_DIR, { recursive: true });

const schemaFiles = readdirSync(SCHEMA_DIR)
  .filter((fileName) => fileName.endsWith(".schema.json"))
  .sort();

schemaFiles.forEach((schemaFileName) => {
  const outputFileName = FILE_NAME_MAP.get(schemaFileName);

  if (outputFileName === undefined) {
    throw new Error(`No TypeScript output mapping for ${schemaFileName}`);
  }

  const schema = readJson(join(SCHEMA_DIR, schemaFileName));
  writeFileSync(join(OUT_DIR, outputFileName), renderFile(schemaFileName, schema));
});

const exportFiles = schemaFiles
  .map((schemaFileName) => FILE_NAME_MAP.get(schemaFileName))
  .filter((fileName): fileName is string => fileName !== undefined)
  .map((fileName) => basename(fileName, ".ts"))
  .sort();

const indexContent = `${HEADER}${exportFiles
  .map((fileName) => `export type * from "./${fileName}";`)
  .join("\n")}\n`;

writeFileSync(join(OUT_DIR, "index.ts"), indexContent);

console.log(`Generated TypeScript contracts in ${OUT_DIR}`);
