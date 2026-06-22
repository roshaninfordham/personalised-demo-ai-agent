import fs from "node:fs";
import path from "node:path";

const root = path.resolve(__dirname, "../..");
const runtimeFile = path.join(root, ".local/runtime/ports.env");

function readRuntimeEnv(): Record<string, string> {
  if (!fs.existsSync(runtimeFile)) return {};
  return Object.fromEntries(
    fs
      .readFileSync(runtimeFile, "utf8")
      .split(/\r?\n/u)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#") && line.includes("="))
      .map((line) => {
        const [key, ...rest] = line.split("=");
        return [key, rest.join("=").replace(/^['"]|['"]$/gu, "")];
      }),
  );
}

const runtimeEnv = readRuntimeEnv();

export function runtimeValue(key: string, fallback: string): string {
  return process.env[key] ?? runtimeEnv[key] ?? fallback;
}

export const webBaseUrl = runtimeValue(
  "E2E_BASE_URL",
  runtimeValue("WEB_URL", "http://localhost:3000"),
);
export const apiBaseUrl = runtimeValue(
  "NEXT_PUBLIC_API_BASE_URL",
  runtimeValue("API_URL", "http://localhost:8000"),
);
