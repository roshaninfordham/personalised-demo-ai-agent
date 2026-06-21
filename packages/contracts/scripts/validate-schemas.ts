import Ajv2020 from "ajv/dist/2020";
import { readFileSync, readdirSync } from "node:fs";
import { basename, join } from "node:path";
import { fileURLToPath } from "node:url";

const CONTRACTS_ROOT = fileURLToPath(new URL("..", import.meta.url));
const SCHEMA_DIR = join(CONTRACTS_ROOT, "schemas");

const EXPECTED_FILES = [
  "browser-action.schema.json",
  "common.schema.json",
  "demo-graph.schema.json",
  "demo-recipe.schema.json",
  "demo-session.schema.json",
  "event.schema.json",
  "generated-route.schema.json",
  "knowledge-retrieval.schema.json",
  "lead-summary.schema.json",
  "learner-job.schema.json",
  "product-learning.schema.json",
  "screen-state.schema.json",
  "transcript.schema.json",
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

function requireString(schema: JsonObject, key: string, path: string): string {
  const value = schema[key];

  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`${path} must define string ${key}`);
  }

  return value;
}

function requireArray(schema: JsonObject, key: string, path: string): void {
  if (!Array.isArray(schema[key])) {
    throw new Error(`${path} must define array ${key}`);
  }
}

function checkObjectSchemas(value: unknown, path: string): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      checkObjectSchemas(item, `${path}[${String(index)}]`);
    });
    return;
  }

  if (!isObject(value)) {
    return;
  }

  if (value.type === "object" && !Object.hasOwn(value, "additionalProperties")) {
    throw new Error(`${path} has type object but does not define additionalProperties`);
  }

  Object.entries(value).forEach(([key, child]) => {
    checkObjectSchemas(child, `${path}.${key}`);
  });
}

const actualFiles = readdirSync(SCHEMA_DIR)
  .filter((fileName) => fileName.endsWith(".schema.json"))
  .sort();

if (JSON.stringify(actualFiles) !== JSON.stringify(EXPECTED_FILES)) {
  throw new Error(
    `Schema filenames do not match expected set. Expected ${EXPECTED_FILES.join(", ")} but got ${actualFiles.join(", ")}`,
  );
}

const schemas = actualFiles.map((fileName) => {
  const path = join(SCHEMA_DIR, fileName);
  const schema = readJson(path);
  const schemaId = requireString(schema, "$id", fileName);

  requireString(schema, "$schema", fileName);
  requireString(schema, "title", fileName);
  requireString(schema, "type", fileName);
  requireArray(schema, "required", fileName);
  checkObjectSchemas(schema, basename(path));

  return { fileName, schemaId, schema };
});

const ids = new Set<string>();
schemas.forEach(({ fileName, schemaId }) => {
  if (ids.has(schemaId)) {
    throw new Error(`Duplicate schema $id found in ${fileName}: ${schemaId}`);
  }
  ids.add(schemaId);
});

const ajv = new Ajv2020({
  allErrors: true,
  strict: false,
  validateFormats: false,
});

schemas.forEach(({ schema }) => {
  ajv.addSchema(schema);
});

schemas.forEach(({ schemaId }) => {
  const validate = ajv.getSchema(schemaId);

  if (validate === undefined) {
    throw new Error(`AJV did not register schema ${schemaId}`);
  }
});

console.log(`Validated ${String(schemas.length)} contract schemas.`);
