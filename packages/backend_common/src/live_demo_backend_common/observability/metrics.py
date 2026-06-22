"""Prometheus-compatible metrics with cardinality guardrails."""

from __future__ import annotations

import re
import threading
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from live_demo_backend_common.observability.metric_names import (
    ALL_METRIC_NAMES,
    ALLOWED_LABEL_NAMES,
)

MetricKind = Literal["counter", "gauge", "histogram"]

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
URL_RE = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)
HEX_TRACE_RE = re.compile(r"^[0-9a-f]{16,64}$", re.IGNORECASE)

DEFAULT_BUCKETS = (
    0.0005,
    0.001,
    0.0025,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
    60.0,
)


class MetricCardinalityError(ValueError):
    """Raised when a metric label would create unsafe cardinality."""


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    kind: MetricKind
    description: str
    label_names: tuple[str, ...]
    buckets: tuple[float, ...] = DEFAULT_BUCKETS


@dataclass
class HistogramState:
    observations: list[float] = field(default_factory=list)


class MetricRegistry:
    def __init__(
        self,
        *,
        service: str,
        environment: str,
        guard_enabled: bool = True,
    ) -> None:
        self.service = service
        self.environment = environment
        self.guard_enabled = guard_enabled
        self._definitions: dict[str, MetricDefinition] = {}
        self._counters: defaultdict[tuple[str, tuple[tuple[str, str], ...]], float] = (
            defaultdict(float)
        )
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._histograms: defaultdict[
            tuple[str, tuple[tuple[str, str], ...]], HistogramState
        ] = defaultdict(HistogramState)
        self._lock = threading.Lock()

    def register(self, definition: MetricDefinition) -> None:
        if definition.name not in ALL_METRIC_NAMES:
            raise ValueError(f"Unknown metric name: {definition.name}")
        for label in definition.label_names:
            if label not in ALLOWED_LABEL_NAMES:
                raise MetricCardinalityError(f"Metric label is not allowed: {label}")
        self._definitions[definition.name] = definition

    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Mapping[str, object] | None = None,
    ) -> None:
        definition = self._definition(name, "counter", tuple((labels or {}).keys()))
        label_key = self._label_key(definition, labels or {})
        with self._lock:
            self._counters[(name, label_key)] += value

    def set_gauge(
        self, name: str, value: float, labels: Mapping[str, object] | None = None
    ) -> None:
        definition = self._definition(name, "gauge", tuple((labels or {}).keys()))
        label_key = self._label_key(definition, labels or {})
        with self._lock:
            self._gauges[(name, label_key)] = value

    def observe(
        self,
        name: str,
        value: float,
        labels: Mapping[str, object] | None = None,
    ) -> None:
        definition = self._definition(name, "histogram", tuple((labels or {}).keys()))
        label_key = self._label_key(definition, labels or {})
        with self._lock:
            self._histograms[(name, label_key)].observations.append(value)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    key: tuple(state.observations) for key, state in self._histograms.items()
                },
            }

    def render_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            for (name, labels), value in sorted(self._counters.items()):
                lines.append(f"{name}{_format_labels(labels)} {value:g}")
            for (name, labels), value in sorted(self._gauges.items()):
                lines.append(f"{name}{_format_labels(labels)} {value:g}")
            for (name, labels), state in sorted(self._histograms.items()):
                definition = self._definitions[name]
                count = len(state.observations)
                total = sum(state.observations)
                for bucket in definition.buckets:
                    bucket_count = sum(
                        1 for observation in state.observations if observation <= bucket
                    )
                    bucket_labels = tuple((*labels, ("le", f"{bucket:g}")))
                    lines.append(f"{name}_bucket{_format_labels(bucket_labels)} {bucket_count}")
                inf_labels = tuple((*labels, ("le", "+Inf")))
                lines.append(f"{name}_bucket{_format_labels(inf_labels)} {count}")
                lines.append(f"{name}_count{_format_labels(labels)} {count}")
                lines.append(f"{name}_sum{_format_labels(labels)} {total:g}")
        return "\n".join(lines) + "\n"

    def _definition(
        self,
        name: str,
        kind: MetricKind,
        labels: tuple[str, ...],
    ) -> MetricDefinition:
        definition = self._definitions.get(name)
        if definition is None:
            definition = MetricDefinition(
                name=name,
                kind=kind,
                description=name,
                label_names=tuple(sorted({"service", "environment", *labels})),
            )
            self.register(definition)
        if definition.kind != kind:
            raise ValueError(f"Metric {name} is registered as {definition.kind}, not {kind}")
        return definition

    def _label_key(
        self,
        definition: MetricDefinition,
        labels: Mapping[str, object],
    ) -> tuple[tuple[str, str], ...]:
        normalized = {
            "service": self.service,
            "environment": self.environment,
            **{key: _normalize_value(value) for key, value in labels.items()},
        }
        if self.guard_enabled:
            validate_metric_labels(normalized)
        keys = tuple(sorted(definition.label_names))
        return tuple((key, normalized.get(key, "unknown")) for key in keys)


def validate_metric_labels(labels: Mapping[str, object]) -> None:
    for name, value in labels.items():
        if name not in ALLOWED_LABEL_NAMES:
            raise MetricCardinalityError(f"Metric label is not allowed: {name}")
        text = _normalize_value(value)
        if len(text) > 100:
            raise MetricCardinalityError(f"Metric label value is too long: {name}")
        if UUID_RE.fullmatch(text) or EMAIL_RE.fullmatch(text) or URL_RE.match(text):
            raise MetricCardinalityError(f"Metric label value is high-cardinality: {name}")
        high_cardinality_names = {"trace_id", "session_id", "turn_id", "user_id", "email"}
        if name.endswith("_id") or name in high_cardinality_names:
            raise MetricCardinalityError(f"Metric label name is high-cardinality: {name}")
        if HEX_TRACE_RE.fullmatch(text) and name not in {"error_code"}:
            raise MetricCardinalityError(f"Metric label value looks like an ID: {name}")


_global_registry = MetricRegistry(service="unknown", environment="local")


def configure_global_registry(
    *,
    service: str,
    environment: str,
    guard_enabled: bool = True,
) -> MetricRegistry:
    global _global_registry
    _global_registry = MetricRegistry(
        service=service, environment=environment, guard_enabled=guard_enabled
    )
    return _global_registry


def get_global_registry() -> MetricRegistry:
    return _global_registry


def _normalize_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip().lower().replace(" ", "_")
    return text or "unknown"


def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    escaped = ",".join(
        f'{key}="{value.replace(chr(34), chr(92) + chr(34))}"' for key, value in labels
    )
    return "{" + escaped + "}"
