"""W3C trace context propagation helpers."""

from __future__ import annotations

import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass

TRACEPARENT_RE = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
HEX_32_RE = re.compile(r"^[0-9a-f]{32}$")
HEX_16_RE = re.compile(r"^[0-9a-f]{16}$")


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    trace_flags: str = "01"

    @property
    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"

    @classmethod
    def new(cls) -> TraceContext:
        return cls(trace_id=secrets.token_hex(16), span_id=secrets.token_hex(8))

    @classmethod
    def from_traceparent(cls, value: str | None) -> TraceContext | None:
        if value is None:
            return None
        match = TRACEPARENT_RE.fullmatch(value.strip().lower())
        if match is None:
            return None
        return cls(trace_id=match.group(1), span_id=match.group(2), trace_flags=match.group(3))

    @classmethod
    def from_headers(cls, headers: Mapping[str, str | bytes | object]) -> TraceContext:
        lower_headers = {str(key).lower(): value for key, value in headers.items()}
        traceparent = _to_str(lower_headers.get("traceparent"))
        context = cls.from_traceparent(traceparent)
        if context is not None:
            return context
        trace_id = _to_str(lower_headers.get("x-trace-id"))
        if trace_id and HEX_32_RE.fullmatch(trace_id.lower()):
            return cls(trace_id=trace_id.lower(), span_id=secrets.token_hex(8))
        return cls.new()

    def child(self) -> TraceContext:
        return TraceContext(
            trace_id=self.trace_id,
            span_id=secrets.token_hex(8),
            trace_flags=self.trace_flags,
        )

    def inject_headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        output = dict(headers or {})
        output["traceparent"] = self.traceparent
        output["x-trace-id"] = self.trace_id
        return output

    def inject_carrier(self, carrier: dict[str, str] | None = None) -> dict[str, str]:
        output = dict(carrier or {})
        output["traceparent"] = self.traceparent
        output["trace_id"] = self.trace_id
        output["span_id"] = self.span_id
        return output


def extract_trace_context(carrier: Mapping[str, str | bytes | object]) -> TraceContext:
    return TraceContext.from_headers(carrier)


def _to_str(value: str | bytes | object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return str(value)
