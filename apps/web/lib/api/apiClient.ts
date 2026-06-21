import type { ApiErrorResponse } from "@live-demo-agent/contracts";

import { getPublicConfig } from "../config/publicConfig";
import { createRequestId } from "../utils/ids";
import { ApiClientError, type ApiError } from "./apiErrors";

export type ApiClientOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeoutMs?: number;
};

const localOrgId = "00000000-0000-0000-0000-000000000001";

export async function apiRequest<T>(endpoint: string, options: ApiClientOptions = {}): Promise<T> {
  if (/^https?:\/\//i.test(endpoint)) {
    throw new ApiClientError({
      code: "absolute_endpoint_rejected",
      message: "Frontend API calls must use relative endpoints.",
      status: 0,
    });
  }
  const config = getPublicConfig();
  const controller = new AbortController();
  const timeout = setTimeout(() => {
    controller.abort();
  }, options.timeoutMs ?? 15_000);
  const signal = composeSignal(options.signal, controller.signal);
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Request-ID": createRequestId(),
    "X-Organization-ID": localOrgId,
    ...(options.headers ?? {}),
  };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";

  try {
    const init: RequestInit = {
      method: options.method ?? "GET",
      headers,
      signal,
    };
    if (options.body !== undefined) init.body = JSON.stringify(options.body);
    const response = await fetch(`${config.apiBaseUrl}${endpoint}`, init);
    const payload = await readResponse(response);
    if (!response.ok) {
      throw new ApiClientError(normalizeApiError(response.status, payload));
    }
    return payload as T;
  } catch (error) {
    if (error instanceof ApiClientError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiClientError({ code: "request_timeout", message: "Request timed out.", status: 0 });
    }
    throw new ApiClientError({ code: "network_error", message: "API request failed.", status: 0 });
  } finally {
    clearTimeout(timeout);
  }
}

async function readResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json() as Promise<unknown>;
  }
  const text = await response.text();
  return text === "" ? null : { message: text };
}

function normalizeApiError(status: number, payload: unknown): ApiError {
  if (isApiErrorResponse(payload)) {
    return {
      code: payload.error.code,
      message: payload.error.message,
      requestId: payload.error.request_id,
      traceId: payload.error.trace_id,
      status,
      details: payload.error.details,
    };
  }
  return { code: "api_error", message: "API request failed.", status, details: payload };
}

function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as ApiErrorResponse).error.code === "string"
  );
}

function composeSignal(left: AbortSignal | undefined, right: AbortSignal): AbortSignal {
  if (left === undefined) return right;
  const controller = new AbortController();
  const abort = (): void => {
    controller.abort();
  };
  left.addEventListener("abort", abort, { once: true });
  right.addEventListener("abort", abort, { once: true });
  return controller.signal;
}
