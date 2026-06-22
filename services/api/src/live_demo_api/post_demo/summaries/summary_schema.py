"""Lead summary schema helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID


def empty_summary(
    *,
    session_id: UUID,
    product_id: UUID,
    generation_mode: str = "deterministic",
) -> dict[str, object]:
    return {
        "session_id": str(session_id),
        "product_id": str(product_id),
        "summary_version": "v1",
        "generation_mode": generation_mode,
        "lead": {"name": None, "email": None, "company": None, "role": None},
        "demo_summary": {
            "duration_seconds": 0,
            "features_shown": [],
            "questions_asked": [],
            "screens_visited_count": 0,
            "browser_actions_count": 0,
            "recipe_steps_completed": 0,
            "recipe_steps_total": 0,
        },
        "qualification": {
            "pain_points": [],
            "use_cases": [],
            "objections": [],
            "buying_signals": [],
            "urgency": {"level": "unknown", "confidence": 0.0, "evidence": []},
            "feature_interests": [],
            "unanswered_questions": [],
            "overall_score": 0,
            "confidence": 0.0,
        },
        "recommended_follow_up": {
            "summary": "Follow up with a concise recap of verified product areas shown.",
            "suggested_next_steps": [],
            "assets_to_send": [],
            "owner_notes": [],
        },
        "evidence_summary": {
            "transcript_event_ids": [],
            "browser_action_ids": [],
            "screen_ids": [],
            "recipe_step_ids": [],
        },
        "redaction": {
            "redaction_applied": False,
            "visual_redaction_applied": False,
            "notes": [],
        },
        "created_at": datetime.now(UTC).isoformat(),
    }
