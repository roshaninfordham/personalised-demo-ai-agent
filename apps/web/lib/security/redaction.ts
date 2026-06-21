const sensitive = /(authorization|cookie|api_key|token|secret|password|client_secret|refresh_token|access_token)/i;

export function redactRecord(input: Record<string, unknown>): Record<string, unknown> {
  const output: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(input)) {
    if (sensitive.test(key)) {
      output[key] = "***REDACTED***";
    } else if (isRecord(value)) {
      output[key] = redactRecord(value);
    } else {
      output[key] = value;
    }
  }
  return output;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
