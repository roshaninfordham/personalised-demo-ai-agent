from live_demo_contracts.browser_action import BrowserActionCommand, BrowserActionResult
from live_demo_contracts.demo_session import DemoSession
from live_demo_contracts.lead_summary import LeadSummary


def test_generated_python_contracts_validate_sample_payloads() -> None:
    now = "2026-06-20T00:00:00.000Z"
    session_id = "00000000-0000-4000-8000-000000000001"

    session = DemoSession.model_validate(
        {
            "session_id": session_id,
            "product_id": "00000000-0000-4000-8000-000000000002",
            "start_url": "https://example.com",
            "status": "created",
            "current_phase": "created",
            "created_at": now,
            "updated_at": now,
        }
    )

    command = BrowserActionCommand.model_validate(
        {
            "command_id": "00000000-0000-4000-8000-000000000003",
            "session_id": session_id,
            "browser_session_id": "browser-session-1",
            "action_type": "read_current_screen",
            "created_at": now,
        }
    )

    result = BrowserActionResult.model_validate(
        {
            "command_id": command.command_id,
            "session_id": session.session_id,
            "success": True,
            "policy_decision": "allowed",
            "risk_level": "low",
            "latency_ms": 10,
            "created_at": now,
        }
    )

    lead_summary = LeadSummary.model_validate(
        {
            "lead_summary_id": "00000000-0000-4000-8000-000000000004",
            "session_id": session.session_id,
            "demo_summary": {
                "duration_seconds": 0,
                "features_shown": [],
                "questions_asked": [],
                "screens_visited": [],
            },
            "qualification": {
                "insights": [],
                "urgency_level": "unknown",
                "confidence": 0,
            },
            "recommended_follow_up": "Not implemented in Phase 1.",
            "crm_payload": {
                "provider": "mock",
                "objects": [],
            },
            "created_at": now,
        }
    )

    assert result.success is True
    assert lead_summary.session_id == session.session_id
