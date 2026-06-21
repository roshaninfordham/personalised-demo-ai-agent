"""Health checks for the learner worker."""

from __future__ import annotations


def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "learner-worker"}


def readiness_check(enabled: bool = True) -> dict[str, str]:
    return {"status": "ready" if enabled else "disabled", "service": "learner-worker"}
