"""Request context helpers."""

from dataclasses import dataclass
from uuid import uuid4

from fastapi import Request


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str
    trace_id: str


def request_context_from_request(request: Request) -> RequestContext:
    request_id = request.headers.get("x-request-id") or str(uuid4())
    trace_id = request.headers.get("x-trace-id") or request_id
    return RequestContext(request_id=request_id[:128], trace_id=trace_id[:128])
