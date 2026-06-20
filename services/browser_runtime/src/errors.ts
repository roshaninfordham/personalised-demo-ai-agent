export type ErrorEnvelope = {
  error: {
    code: string;
    message: string;
    request_id: string;
    trace_id: string;
    details: Record<string, unknown>;
  };
};

export class BrowserRuntimeError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: number,
    public readonly details: Record<string, unknown> = {},
  ) {
    super(message);
  }
}

export function errorEnvelope(
  error: BrowserRuntimeError,
  requestId: string,
  traceId: string,
): ErrorEnvelope {
  return {
    error: {
      code: error.code,
      message: error.message,
      request_id: requestId,
      trace_id: traceId,
      details: error.details,
    },
  };
}

export function notFound(message = "Browser session not found."): BrowserRuntimeError {
  return new BrowserRuntimeError("browser_session_not_found", message, 404);
}

