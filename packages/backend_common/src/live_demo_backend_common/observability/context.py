"""Typed telemetry context shared across tracing, logging, and events."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetryContext:
    trace_id: str
    request_id: str | None = None
    organization_id: str | None = None
    product_id: str | None = None
    session_id: str | None = None
    turn_id: str | None = None
    voice_session_id: str | None = None
    browser_session_id: str | None = None
    command_id: str | None = None
    action_id: str | None = None
    screen_id: str | None = None

    def log_fields(self) -> dict[str, str]:
        return {
            key: value
            for key, value in {
                "trace_id": self.trace_id,
                "request_id": self.request_id,
                "organization_id": self.organization_id,
                "product_id": self.product_id,
                "session_id": self.session_id,
                "turn_id": self.turn_id,
                "voice_session_id": self.voice_session_id,
                "browser_session_id": self.browser_session_id,
                "command_id": self.command_id,
                "action_id": self.action_id,
                "screen_id": self.screen_id,
            }.items()
            if value
        }
