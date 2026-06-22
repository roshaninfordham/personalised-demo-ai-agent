const sensitiveKey = /authorization|cookie|token|secret|password|api_key|prompt|transcript/i;

export function clientLog(eventType: string, fields: Record<string, unknown> = {}): string {
  return JSON.stringify({
    timestamp: new Date().toISOString(),
    level: "info",
    service: "web",
    environment: process.env.NEXT_PUBLIC_APP_ENV ?? "local",
    event_type: eventType,
    metadata: redact(fields),
  });
}

function redact(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(redact);
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [
        key,
        sensitiveKey.test(key) ? "***REDACTED***" : redact(item),
      ]),
    );
  }
  return value;
}
