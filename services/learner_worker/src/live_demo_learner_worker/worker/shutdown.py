"""Graceful shutdown state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ShutdownState:
    draining: bool = False

    def request_stop(self) -> None:
        self.draining = True
