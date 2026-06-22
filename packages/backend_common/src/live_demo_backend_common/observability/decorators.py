"""Latency instrumentation decorators."""

from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable, Mapping
from typing import ParamSpec, TypeVar

from live_demo_backend_common.observability.latency_enforcer import (
    LatencyEnforcer,
    async_latency_observer,
    latency_observer,
)
from live_demo_backend_common.observability.trace_context import TraceContext
from live_demo_backend_common.observability.tracing import start_span

P = ParamSpec("P")
R = TypeVar("R")


def observe_latency(
    operation: str,
    *,
    enforcer: LatencyEnforcer | None = None,
    context: Mapping[str, object] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with latency_observer(operation, enforcer=enforcer, context=context):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def observe_async_latency(
    operation: str,
    *,
    enforcer: LatencyEnforcer | None = None,
    context: Mapping[str, object] | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async with async_latency_observer(operation, enforcer=enforcer, context=context):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def trace_async_span(name: str) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            request = _find_request(args, kwargs)
            trace_id = str(getattr(request, "trace_id", "")) if request is not None else ""
            trace_context = (
                TraceContext(trace_id=trace_id, span_id=TraceContext.new().span_id)
                if len(trace_id) == 32
                else None
            )
            attributes = _request_attributes(request)
            with start_span(name, trace_context=trace_context, attributes=attributes):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def _find_request(args: tuple[object, ...], kwargs: Mapping[str, object]) -> object | None:
    if "request" in kwargs:
        return kwargs["request"]
    for value in args:
        if hasattr(value, "trace_id") and hasattr(value, "session_id"):
            return value
    return None


def _request_attributes(request: object | None) -> dict[str, object]:
    if request is None:
        return {}
    fields = {
        "live_demo.organization_id": getattr(request, "organization_id", None),
        "live_demo.session_id": getattr(request, "session_id", None),
        "live_demo.operation": request.__class__.__name__,
    }
    return {key: str(value) for key, value in fields.items() if value is not None}
