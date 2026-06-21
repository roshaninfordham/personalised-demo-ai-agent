from uuid import uuid4

from live_demo_api.orchestration.orchestration_shutdown import (
    deterministic_summary_payload,
    ordered_cleanup_resources,
)
from live_demo_api.orchestration.orchestration_types import SessionResource


def test_shutdown_cleanup_order_is_deterministic() -> None:
    resources = (
        SessionResource("redis_live_state", "redis", "redis", "ready"),
        SessionResource("browser_session", str(uuid4()), "browser_runtime", "ready"),
        SessionResource("voice_session", str(uuid4()), "agent_runtime", "ready"),
        SessionResource("learner_run", str(uuid4()), "learner_worker", "ready"),
    )

    ordered = ordered_cleanup_resources(resources)

    assert [resource.resource_type for resource in ordered] == [
        "voice_session",
        "browser_session",
        "learner_run",
        "redis_live_state",
    ]


def test_deterministic_summary_does_not_hallucinate_features() -> None:
    session_id = uuid4()

    summary = deterministic_summary_payload(session_id=session_id)

    assert summary["session_id"] == str(session_id)
    assert summary["summary_type"] == "deterministic_phase_12"
    assert summary["features_shown"] == []
    assert summary["questions_detected"] == []
