"""HTTP middleware for request IDs, trace IDs, timing, and logging."""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from live_demo_api.config import ApiSettings
from live_demo_api.logging_config import request_id_var, trace_id_var

ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
logger = logging.getLogger(__name__)


def _clean_header_id(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not ID_RE.fullmatch(stripped):
        return None
    return stripped


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _clean_header_id(request.headers.get("x-request-id")) or str(uuid4())
        trace_id = _clean_header_id(request.headers.get("x-trace-id")) or request_id
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        token_request = request_id_var.set(request_id)
        token_trace = trace_id_var.set(trace_id)
        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.monotonic() - start) * 1000, 3)
            logger.exception(
                "http.request.failed",
                extra={
                    "event": "http.request.failed",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise
        finally:
            request_id_var.reset(token_request)
            trace_id_var.reset(token_trace)
        duration_ms = round((time.monotonic() - start) * 1000, 3)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Process-Time-MS"] = str(duration_ms)
        logger.info(
            "http.request.completed",
            extra={
                "event": "http.request.completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


def setup_middleware(app: FastAPI, settings: ApiSettings) -> None:
    origins = [
        origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
