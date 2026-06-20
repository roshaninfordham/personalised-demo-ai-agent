"""Application errors and FastAPI exception handlers."""

from __future__ import annotations

import logging
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    code = "internal_error"
    safe_message = "Internal server error."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message or self.safe_message)
        self.safe_message = message or self.safe_message
        self.code = code or self.code
        self.details = details or {}


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"
    safe_message = "Validation error."


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    safe_message = "Resource not found."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    safe_message = "Conflict."


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"
    safe_message = "Forbidden."


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    safe_message = "Unauthorized."


class DependencyUnavailableError(AppError):
    status_code = 503
    code = "dependency_unavailable"
    safe_message = "Dependency unavailable."


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"
    safe_message = "Rate limit exceeded."


class StateTransitionError(AppError):
    status_code = 409
    code = "invalid_state_transition"
    safe_message = "Invalid state transition."


class PolicyViolationError(AppError):
    status_code = 403
    code = "policy_violation"
    safe_message = "Policy violation."


def error_payload(
    request: Request, code: str, message: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", ""),
            "trace_id": getattr(request.state, "trace_id", ""),
            "details": details or {},
        }
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(request, exc.code, exc.safe_message, exc.details),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_payload(
            request,
            "request_validation_error",
            "Request validation failed.",
            {
                "errors": [
                    {"loc": list(error["loc"]), "type": error["type"]} for error in exc.errors()
                ]
            },
        ),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API exception", extra={"event": "http.request.failed"})
    return JSONResponse(
        status_code=500,
        content=error_payload(request, "internal_error", "Internal server error."),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, cast(Any, app_error_handler))
    app.add_exception_handler(RequestValidationError, cast(Any, validation_error_handler))
    app.add_exception_handler(Exception, cast(Any, unhandled_error_handler))
