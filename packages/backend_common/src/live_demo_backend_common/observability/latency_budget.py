"""Central latency budget definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LatencyBudget:
    operation: str
    target_ms: float
    warning_ms: float
    critical_ms: float
    hot_path: bool
    enabled: bool = True


DEFAULT_LATENCY_BUDGETS: dict[str, LatencyBudget] = {
    "context_build": LatencyBudget("context_build", 50, 100, 250, True),
    "llm_realtime_host": LatencyBudget("llm_realtime_host", 900, 1500, 3000, True),
    "first_audio": LatencyBudget("first_audio", 900, 1500, 3000, True),
    "stt_partial": LatencyBudget("stt_partial", 400, 750, 1500, True),
    "stt_final": LatencyBudget("stt_final", 800, 1500, 3000, True),
    "tts_first_audio": LatencyBudget("tts_first_audio", 500, 1000, 2000, True),
    "browser_action_validation": LatencyBudget(
        "browser_action_validation", 50, 100, 250, True
    ),
    "browser_action_total": LatencyBudget("browser_action_total", 1000, 3000, 5000, True),
    "screen_read": LatencyBudget("screen_read", 800, 2000, 5000, True),
    "event_publish": LatencyBudget("event_publish", 20, 100, 250, True),
    "event_lag": LatencyBudget("event_lag", 250, 1000, 5000, True),
    "interruption_stop_tts": LatencyBudget("interruption_stop_tts", 150, 250, 500, True),
}
