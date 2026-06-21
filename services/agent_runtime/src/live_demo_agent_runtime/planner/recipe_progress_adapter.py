from __future__ import annotations

from typing import Any


def progress_brief(progress_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "active_step_key": progress_payload.get("active_step_key"),
        "completed": progress_payload.get("completed_count", 0),
        "total": progress_payload.get("total_count", 0),
        "progress_ratio": progress_payload.get("progress_ratio", 0.0),
    }
