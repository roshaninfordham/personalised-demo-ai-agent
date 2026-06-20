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


def test_lead_insights_endpoint_returns_stored_insights(api_client: TestClient) -> None:
    session = _seed_session(api_client)
    transcript_id = str(uuid4())
    insight_id = str(uuid4())
    db_execute(
        """
        insert into transcript_events (
          transcript_event_id, organization_id, session_id, speaker, chunk_type, text, is_final
        ) values (
          cast(:transcript_id as uuid), cast(:organization_id as uuid), cast(:session_id as uuid),
          'user', 'final', 'We need faster reporting.', true
        )
        """,
        {
            "transcript_id": transcript_id,
            "organization_id": ORG_ID,
            "session_id": session["session_id"],
        },
    )
    db_execute(
        """
        insert into lead_insights (
          insight_id, organization_id, session_id, insight_type, content, confidence,
          evidence_transcript_event_ids
        ) values (
          cast(:insight_id as uuid), cast(:organization_id as uuid), cast(:session_id as uuid),
          'question', 'Can it filter reports?', 0.900, ARRAY[cast(:transcript_id as uuid)]
        )
        """,
        {
            "insight_id": insight_id,
            "organization_id": ORG_ID,
            "session_id": session["session_id"],
            "transcript_id": transcript_id,
        },
    )
    response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/lead-insights?insight_type=question",
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["insight_id"] == insight_id


def test_lead_summary_endpoint_returns_existing_summary(api_client: TestClient) -> None:
    session = _seed_session(api_client)
    summary = {
        "demo_summary": {
            "duration_seconds": 10,
            "features_shown": [],
            "questions_asked": [],
            "screens_visited": [],
        },
        "qualification": {"insights": [], "urgency_level": "unknown", "confidence": 0.0},
        "recommended_follow_up": "Send a concise recap.",
        "crm_payload": {"provider": "mock", "objects": []},
    }
    db_execute(
        """
        insert into lead_summaries (
          lead_summary_id, organization_id, session_id, summary, confidence
        ) values (
          cast(:lead_summary_id as uuid), cast(:organization_id as uuid), cast(:session_id as uuid),
          cast(:summary as jsonb), 0.700
        )
        """,
        {
            "lead_summary_id": str(uuid4()),
            "organization_id": ORG_ID,
            "session_id": session["session_id"],
            "summary": json.dumps(summary),
        },
    )
    response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/lead-summary", headers=HEADERS
    )
    assert response.status_code == 200
    assert response.json()["lead_summary"]["recommended_follow_up"] == "Send a concise recap."

    crm_response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/crm-payload", headers=HEADERS
    )
    assert crm_response.status_code == 200
    assert crm_response.json()["crm_payload"]["provider"] == "mock"


def test_missing_lead_summary_returns_404(api_client: TestClient) -> None:
    session = _seed_session(api_client)
    response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/lead-summary", headers=HEADERS
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "lead_summary_not_found"


def test_missing_crm_payload_returns_404(api_client: TestClient) -> None:
    session = _seed_session(api_client)
    response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/crm-payload", headers=HEADERS
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "lead_summary_not_found"
