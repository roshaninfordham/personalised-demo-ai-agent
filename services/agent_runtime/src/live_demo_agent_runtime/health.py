"""Health response helpers."""

from datetime import UTC, datetime


def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "agent-runtime",
        "checked_at": datetime.now(UTC).isoformat(),
    }
