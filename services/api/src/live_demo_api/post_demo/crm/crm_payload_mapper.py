"""Map lead summaries into generic CRM payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from live_demo_api.db.models import DemoSession, LeadSummary, Product


class CrmPayloadMapper:
    def map_payload(
        self,
        *,
        lead_summary: LeadSummary,
        session: DemoSession,
        product: Product,
    ) -> dict[str, Any]:
        summary = lead_summary.summary
        qualification = _dict(summary.get("qualification"))
        demo = _dict(summary.get("demo_summary"))
        lead = _dict(summary.get("lead"))
        role = lead.get("role")
        role_value = role.get("value") if isinstance(role, dict) else role
        follow_up = _dict(summary.get("recommended_follow_up"))
        evidence = _dict(summary.get("evidence_summary"))
        return {
            "schema_version": "v1",
            "session_id": str(session.session_id),
            "product_id": str(product.product_id),
            "lead": {
                "name": session.user_display_name,
                "email": session.user_email,
                "company": session.user_company,
                "role": role_value,
            },
            "demo": {
                "duration_seconds": demo.get("duration_seconds", 0),
                "features_shown": [
                    item.get("feature_label")
                    for item in _list(demo.get("features_shown"))[:100]
                    if isinstance(item, dict) and item.get("feature_label")
                ],
                "questions_asked": _list(demo.get("questions_asked"))[:20],
                "screens_visited_count": demo.get("screens_visited_count", 0),
                "browser_actions_count": demo.get("browser_actions_count", 0),
                "transcript_url": None,
                "recording_url": None,
            },
            "qualification": {
                "score": qualification.get("overall_score", 0),
                "confidence": qualification.get("confidence", 0.0),
                "pain_points": _top_contents(qualification.get("pain_points")),
                "objections": _top_contents(qualification.get("objections")),
                "buying_signals": _top_contents(qualification.get("buying_signals")),
                "urgency": _dict(qualification.get("urgency")).get("level", "unknown"),
                "feature_interests": _top_contents(qualification.get("feature_interests")),
                "unanswered_questions": _top_contents(qualification.get("unanswered_questions")),
            },
            "recommended_follow_up": {
                "summary": follow_up.get("summary", ""),
                "suggested_next_steps": _list(follow_up.get("suggested_next_steps")),
                "assets_to_send": _list(follow_up.get("assets_to_send")),
                "owner_notes": _list(follow_up.get("owner_notes")),
            },
            "evidence": {
                "lead_summary_id": str(lead_summary.lead_summary_id),
                "transcript_event_ids": _list(evidence.get("transcript_event_ids")),
                "browser_action_ids": _list(evidence.get("browser_action_ids")),
                "screen_ids": _list(evidence.get("screen_ids")),
            },
            "metadata": {
                "generated_at": datetime.now(UTC).isoformat(),
                "source": "live-demo-agent",
                "dry_run": True,
            },
        }


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _top_contents(value: object) -> list[str]:
    output: list[str] = []
    for item in _list(value)[:10]:
        if isinstance(item, dict) and isinstance(item.get("content"), str):
            output.append(item["content"])
        elif isinstance(item, str):
            output.append(item)
    return output
