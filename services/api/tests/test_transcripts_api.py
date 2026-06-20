from __future__ import annotations

import json
from uuid import uuid4

from fastapi.testclient import TestClient

from services.api.tests.helpers import (
    HEADERS,
    ORG_ID,
    create_demo_session,
    create_product,
    db_execute,
)


def _seed_session(api_client: TestClient) -> dict[str, object]:
    product = create_product(api_client)
    return create_demo_session(api_client, str(product["product_id"]))


def test_fetch_transcript_returns_ordered_events(api_client: TestClient) -> None:
    session = _seed_session(api_client)
    first_id = str(uuid4())
    second_id = str(uuid4())
    for event_id, text in [
        (first_id, "What does this show?"),
        (second_id, "It shows the overview."),
    ]:
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
                "event_id": event_id,
                "organization_id": ORG_ID,
                "session_id": session["session_id"],
                "speaker": "user" if text.endswith("?") else "assistant",
                "text": text,
            },
        )

    response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/transcript?limit=100",
        headers=HEADERS,
    )
    assert response.status_code == 200
    texts = [item["text"] for item in response.json()["items"]]
    assert "What does this show?" in texts
    assert "It shows the overview." in texts


def test_fetch_transcript_supports_pagination(api_client: TestClient) -> None:
    session = _seed_session(api_client)
    for index in range(2):
        db_execute(
            """
            insert into transcript_events (
              transcript_event_id, organization_id, session_id, speaker, chunk_type, text, is_final
            ) values (
              cast(:event_id as uuid), cast(:organization_id as uuid), cast(:session_id as uuid),
              'user', 'final', :text, true
            )
            """,
            {
                "event_id": str(uuid4()),
                "organization_id": ORG_ID,
                "session_id": session["session_id"],
                "text": f"Question {index}?",
            },
        )
    response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/transcript?limit=1",
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["next_cursor"] is not None


def test_browser_actions_hide_payload_by_default_and_allow_admin_include(
    api_client: TestClient,
) -> None:
    session = _seed_session(api_client)
    action_id = str(uuid4())
    db_execute(
        """
        insert into action_events (
          action_event_id, organization_id, session_id, action_type, action_payload,
          risk_level, policy_decision, success, latency_ms
        ) values (
          cast(:action_id as uuid), cast(:organization_id as uuid), cast(:session_id as uuid),
          'click_element', cast(:payload as jsonb), 'low', 'allowed', true, 12
        )
        """,
        {
            "action_id": action_id,
            "organization_id": ORG_ID,
            "session_id": session["session_id"],
            "payload": json.dumps({"element_id": "el_1"}),
        },
    )
    hidden = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/browser-actions",
        headers=HEADERS,
    )
    assert hidden.status_code == 200
    assert hidden.json()["items"][0]["action_payload"] is None

    included = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/browser-actions?include_payload=true",
        headers=HEADERS,
    )
    assert included.status_code == 200
    assert included.json()["items"][0]["action_payload"] == {"element_id": "el_1"}


def test_questions_endpoint_returns_heuristic_questions(api_client: TestClient) -> None:
    session = _seed_session(api_client)
    db_execute(
        """
        insert into transcript_events (
          transcript_event_id, organization_id, session_id, speaker, chunk_type, text, is_final
        ) values (
          cast(:event_id as uuid), cast(:organization_id as uuid), cast(:session_id as uuid),
          'user', 'final', 'Can it filter reports?', true
        )
        """,
        {
            "event_id": str(uuid4()),
            "organization_id": ORG_ID,
            "session_id": session["session_id"],
        },
    )
    response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/questions", headers=HEADERS
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["source"] == "heuristic_transcript"


def test_features_shown_does_not_hallucinate(api_client: TestClient) -> None:
    session = _seed_session(api_client)
    response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/features-shown",
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["features"] == []
    assert response.json()["source"] == "not_available_in_phase_3"
