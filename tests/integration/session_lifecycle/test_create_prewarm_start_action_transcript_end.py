from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from services.api.tests.helpers import (
    HEADERS,
    ORG_ID,
    create_demo_session,
    create_product,
    db_execute,
    db_scalar,
)

pytestmark = pytest.mark.integration


def test_create_prewarm_start_action_transcript_end(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    session_id = str(session["session_id"])

    prewarm = api_client.post(f"/api/v1/demo-sessions/{session_id}/prewarm", headers=HEADERS)
    assert prewarm.status_code == 200, prewarm.text
    prewarm_body = prewarm.json()
    assert prewarm_body["readiness"]["browser_ready"] is True
    assert prewarm_body["readiness"]["first_screen_ready"] is True
    assert prewarm_body["readiness"]["learner_enqueued"] is True
    assert prewarm_body["resources"]["browser_session_id"]

    start = api_client.post(f"/api/v1/demo-sessions/{session_id}/start", headers=HEADERS, json={})
    assert start.status_code == 200, start.text
    start_body = start.json()
    assert _join_config_ready(start_body["join_config"])
    assert "api_key" not in json.dumps(start_body).lower()
    assert "secret" not in json.dumps(start_body).lower()

    _seed_transcript_and_action(session_id)

    transcript = api_client.get(f"/api/v1/demo-sessions/{session_id}/transcript", headers=HEADERS)
    assert transcript.status_code == 200
    transcript_text = " ".join(item["text"] for item in transcript.json()["items"])
    assert "Can you show me the dashboard?" in transcript_text
    assert "I can verify the dashboard." in transcript_text

    actions = api_client.get(f"/api/v1/demo-sessions/{session_id}/browser-actions", headers=HEADERS)
    assert actions.status_code == 200
    assert actions.json()["items"][0]["action_type"] == "click_element"

    end = api_client.post(
        f"/api/v1/demo-sessions/{session_id}/end",
        headers=HEADERS,
        json={"reason": "test_complete"},
    )
    assert end.status_code == 200, end.text
    assert end.json()["session"]["status"] == "completed"

    assert (
        db_scalar(
            "select status from demo_sessions where session_id = cast(:session_id as uuid)",
            {"session_id": session_id},
        )
        == "completed"
    )
    released_resources = _int_scalar(
        db_scalar(
            """
            select count(*) from session_resource_allocations
            where session_id = cast(:session_id as uuid)
              and status in ('released', 'release_failed', 'ready')
            """,
            {"session_id": session_id},
        )
    )
    assert released_resources >= 4
    lifecycle_events = _int_scalar(
        db_scalar(
            """
            select count(*) from session_lifecycle_events
            where session_id = cast(:session_id as uuid)
              and event_type in (
                'session.prewarming.started',
                'session.prewarming.completed',
                'session.ending',
                'session.ended'
              )
            """,
            {"session_id": session_id},
        )
    )
    assert lifecycle_events >= 3


def _seed_transcript_and_action(session_id: str) -> None:
    db_execute(
        """
        insert into transcript_events (
          transcript_event_id, organization_id, session_id, speaker, chunk_type, text, is_final
        ) values
        (
          cast(:user_event_id as uuid),
          cast(:organization_id as uuid),
          cast(:session_id as uuid),
          'user', 'final', 'Can you show me the dashboard?', true
        ),
        (
          cast(:assistant_event_id as uuid),
          cast(:organization_id as uuid),
          cast(:session_id as uuid),
          'assistant', 'final', 'I can verify the dashboard.', true
        )
        """,
        {
            "user_event_id": str(uuid4()),
            "assistant_event_id": str(uuid4()),
            "organization_id": ORG_ID,
            "session_id": session_id,
        },
    )
    db_execute(
        """
        insert into action_events (
          action_event_id, organization_id, session_id, action_type, action_payload,
          risk_level, policy_decision, success, latency_ms
        ) values (
          cast(:action_event_id as uuid), cast(:organization_id as uuid), cast(:session_id as uuid),
          'click_element', cast(:payload as jsonb), 'low', 'allowed', true, 42
        )
        """,
        {
            "action_event_id": str(uuid4()),
            "organization_id": ORG_ID,
            "session_id": session_id,
            "payload": json.dumps({"label": "Dashboard"}),
        },
    )


def _int_scalar(value: object) -> int:
    return value if isinstance(value, int) else 0


def _join_config_ready(join_config: dict[str, object]) -> bool:
    join = join_config.get("join")
    if isinstance(join, dict) and join.get("signaling_url"):
        return True
    return bool(join_config.get("status"))
