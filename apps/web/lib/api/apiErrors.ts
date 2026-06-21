export type ApiError = {
  code: string;
  message: string;
  requestId?: string;
  traceId?: string;
  status: number;
  details?: unknown;
};

export class ApiClientError extends Error {
  constructor(readonly apiError: ApiError) {
    super(apiError.message);
    this.name = "ApiClientError";
  }
}

export function isApiClientError(error: unknown): error is ApiClientError {
  return error instanceof ApiClientError;
}
