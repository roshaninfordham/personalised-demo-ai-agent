import { randomUUID } from "node:crypto";

import type { FastifyRequest } from "fastify";

const allowedHeader = /^[A-Za-z0-9_.-]{1,128}$/;

export type RequestContext = {
  requestId: string;
  traceId: string;
};

export function contextFromRequest(request: FastifyRequest): RequestContext {
  const requestId = safeHeader(request.headers["x-request-id"]) ?? randomUUID();
  const traceId = safeHeader(request.headers["x-trace-id"]) ?? requestId;
  return { requestId, traceId };
}

function safeHeader(value: string | string[] | undefined): string | undefined {
  const candidate = Array.isArray(value) ? value[0] : value;
  if (candidate === undefined || !allowedHeader.test(candidate)) {
    return undefined;
  }
  return candidate;
}

