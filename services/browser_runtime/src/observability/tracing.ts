import { randomBytes } from "node:crypto";

export type TraceContext = {
  traceId: string;
  spanId: string;
  traceparent: string;
};

const traceparentPattern = /^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/u;

export function createTraceContext(traceparent?: string, traceId?: string): TraceContext {
  const parsed = traceparent === undefined ? undefined : traceparentPattern.exec(traceparent);
  const nextTraceId =
    parsed?.[1] ?? (/^[0-9a-f]{32}$/u.test(traceId ?? "") ? traceId ?? "" : randomHex(16));
  const spanId = randomHex(8);
  return {
    traceId: nextTraceId,
    spanId,
    traceparent: `00-${nextTraceId}-${spanId}-01`,
  };
}

export async function withSpan<T>(
  name: string,
  attributes: Record<string, unknown>,
  fn: () => Promise<T>,
): Promise<T> {
  const started = performance.now();
  try {
    return await fn();
  } finally {
    void name;
    void attributes;
    void started;
  }
}

function randomHex(bytes: number): string {
  return randomBytes(bytes).toString("hex");
}
