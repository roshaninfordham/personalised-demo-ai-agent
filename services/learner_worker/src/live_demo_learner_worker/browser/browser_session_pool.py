"""Bounded browser session pool placeholder for the learner worker."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BrowserSessionLease:
    product_id: UUID
    session_key: str


class BrowserSessionPool:
    def __init__(self, max_sessions: int = 2) -> None:
        self._max_sessions = max_sessions
        self._active: dict[UUID, BrowserSessionLease] = {}

    def acquire(self, product_id: UUID) -> BrowserSessionLease:
        existing = self._active.get(product_id)
        if existing is not None:
            return existing
        if len(self._active) >= self._max_sessions:
            raise RuntimeError("No learner browser sessions available.")
        lease = BrowserSessionLease(product_id=product_id, session_key=f"learner:{product_id}")
        self._active[product_id] = lease
        return lease

    def release(self, product_id: UUID) -> None:
        self._active.pop(product_id, None)
