"""Voice latency instrumentation helpers."""

from live_demo_backend_common.observability.latency_enforcer import LatencyEnforcer

voice_latency_enforcer = LatencyEnforcer()

__all__ = ["voice_latency_enforcer"]
