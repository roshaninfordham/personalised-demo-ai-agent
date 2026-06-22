import { AsyncLocalStorage } from "node:async_hooks";

export type LogLevel = "debug" | "info" | "warn" | "error";

export type LogContext = {
  requestId?: string;
  traceId?: string;
  sessionId?: string;
};

const sensitiveKeys = [
  "authorization",
  "cookie",
  "set-cookie",
  "object_storage_secret_key",
  "api_key",
  "token",
  "secret",
  "password",
  "client_secret",
  "refresh_token",
  "access_token",
];

export const logContext = new AsyncLocalStorage<LogContext>();

export class Logger {
  constructor(private readonly level: LogLevel = "info") {}

  debug(message: string, fields: Record<string, unknown> = {}): void {
    this.write("debug", message, fields);
  }

  info(message: string, fields: Record<string, unknown> = {}): void {
    this.write("info", message, fields);
  }

  warn(message: string, fields: Record<string, unknown> = {}): void {
    this.write("warn", message, fields);
  }

  error(message: string, fields: Record<string, unknown> = {}): void {
    this.write("error", message, fields);
  }

  private write(level: LogLevel, message: string, fields: Record<string, unknown>): void {
    if (!this.shouldLog(level)) {
      return;
    }
    const context = logContext.getStore() ?? {};
    const payload = {
      timestamp: new Date().toISOString(),
      level,
      service: "browser-runtime",
      environment: process.env.DEPLOYMENT_ENVIRONMENT ?? process.env.APP_ENV ?? "local",
      event_type: message,
      message,
      request_id: context.requestId,
      trace_id: context.traceId,
      session_id: context.sessionId,
      ...redactRecord(fields),
    };
    const line = JSON.stringify(payload);
    if (level === "error") {
      console.error(line);
    } else {
      console.log(line);
    }
  }

  private shouldLog(level: LogLevel): boolean {
    const rank: Record<LogLevel, number> = { debug: 10, info: 20, warn: 30, error: 40 };
    return rank[level] >= rank[this.level];
  }
}

export function redactRecord(value: Record<string, unknown>): Record<string, unknown> {
  const output: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) {
    if (isSensitiveKey(key)) {
      output[key] = "***REDACTED***";
    } else if (isPlainRecord(item)) {
      output[key] = redactRecord(item);
    } else if (Array.isArray(item)) {
      const items = item as unknown[];
      output[key] = items.map((child) => (isPlainRecord(child) ? redactRecord(child) : child));
    } else {
      output[key] = item;
    }
  }
  return output;
}

function isSensitiveKey(key: string): boolean {
  const normalized = key.toLowerCase();
  return sensitiveKeys.some((pattern) => normalized.includes(pattern));
}

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
