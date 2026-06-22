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

pytestmark = [pytest.mark.integration, pytest.mark.post_demo_integration]


def test_full_post_demo_run_persists_summary_features_insights_and_mock_crm(
    api_client: TestClient,
) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    session_id = str(session["session_id"])
    screen_id = str(uuid4())
    action_id = str(uuid4())

    _insert_transcript(
        session_id,
        "user",
        "I'm a founder and it takes too long to build weekly reports.",
    )
    _insert_transcript(session_id, "user", "Can we export reports this week?")
    _insert_transcript(session_id, "user", "I'm concerned about security.")
    _insert_transcript(
        session_id,
        "assistant",
        "I can't verify security controls from this screen.",
    )
    db_execute(
        """
        insert into screen_snapshots (
          screen_id, organization_id, product_id, session_id, url, url_path, title,
          screen_hash, summary, confidence
        ) values (
          cast(:screen_id as uuid), cast(:organization_id as uuid), cast(:product_id as uuid),
          cast(:session_id as uuid), 'https://example.com/reports', '/reports',
          'Reports', 'reports-screen', 'Reports export and analytics.', 0.900
        )
        """,
        {
            "screen_id": screen_id,
            "organization_id": ORG_ID,
            "product_id": product["product_id"],
            "session_id": session_id,
        },
    )
    db_execute(
        """
        insert into action_events (
          action_event_id, organization_id, session_id, action_type, action_payload,
          risk_level, policy_decision, success, from_screen_id, to_screen_id, latency_ms
        ) values (
          cast(:action_id as uuid), cast(:organization_id as uuid), cast(:session_id as uuid),
          'click_element', cast(:payload as jsonb), 'low', 'allowed', true,
          cast(:screen_id as uuid), cast(:screen_id as uuid), 12
        )
        """,
        {
            "action_id": action_id,
            "organization_id": ORG_ID,
            "session_id": session_id,
            "screen_id": screen_id,
            "payload": json.dumps({"label": "Reports"}),
        },
    )

    response = api_client.post(
        f"/api/v1/demo-sessions/{session_id}/post-demo/run",
        headers=HEADERS,
        json={"run_mode": "full", "export_crm": True, "crm_provider": "mock"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "completed"
    assert db_scalar(
        "select count(*) from lead_insights where session_id = cast(:session_id as uuid)",
        {"session_id": session_id},
    )
    assert db_scalar(
        "select count(*) from features_shown where session_id = cast(:session_id as uuid)",
        {"session_id": session_id},
    )
    assert (
        db_scalar(
            "select count(*) from lead_summaries where session_id = cast(:session_id as uuid)",
            {"session_id": session_id},
        )
        == 1
    )
    assert (
        db_scalar(
            """
        select count(*) from crm_exports
        where session_id = cast(:session_id as uuid)
          and status = 'dry_run_completed'
        """,
            {"session_id": session_id},
        )
        == 1
    )

    features = api_client.get(
        f"/api/v1/demo-sessions/{session_id}/features-shown",
        headers=HEADERS,
    )
    assert features.status_code == 200
    assert features.json()["source"] == "post_demo"
    assert any(item["name"] == "Reporting" for item in features.json()["features"])


def _insert_transcript(session_id: str, speaker: str, text: str) -> None:
    db_execute(
        """
        insert into transcript_events (
          transcript_event_id, organization_id, session_id, speaker, chunk_type, text, is_final
        ) values (
          cast(:event_id as uuid), cast(:organization_id as uuid), cast(:session_id as uuid),
          :speaker, 'final', :text, true
        )
        """,
        {
            "event_id": str(uuid4()),
            "organization_id": ORG_ID,
            "session_id": session_id,
            "speaker": speaker,
            "text": text,
        },
    )
