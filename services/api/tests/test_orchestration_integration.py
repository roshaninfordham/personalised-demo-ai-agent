from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.api.tests.helpers import HEADERS, create_demo_session, create_product, db_scalar

pytestmark = [pytest.mark.integration, pytest.mark.orchestration_integration]


def test_full_prewarm_start_recover_shutdown_flow(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    session_id = str(session["session_id"])

    prewarm = api_client.post(f"/api/v1/demo-sessions/{session_id}/prewarm", headers=HEADERS)

    assert prewarm.status_code == 200, prewarm.text
    prewarm_body = prewarm.json()
    assert prewarm_body["status"] == "waiting_for_user"
    assert prewarm_body["readiness"]["score"] >= 0.7
    assert prewarm_body["resources"]["browser_session_id"]
    assert prewarm_body["resources"]["voice_session_id"]

    start_one = api_client.post(
        f"/api/v1/demo-sessions/{session_id}/start", headers=HEADERS, json={}
    )
    start_two = api_client.post(
        f"/api/v1/demo-sessions/{session_id}/start", headers=HEADERS, json={}
    )

    assert start_one.status_code == 200, start_one.text
    assert start_two.status_code == 200, start_two.text
    assert start_one.json()["session"]["status"] == "waiting_for_user"
    assert start_two.json()["session"]["status"] == "waiting_for_user"

    state = api_client.get(
        f"/api/v1/demo-sessions/{session_id}/orchestration-state", headers=HEADERS
    )
    assert state.status_code == 200, state.text
    assert state.json()["status"] in {"ready", "waiting_for_user"}

    recover = api_client.post(
        f"/api/v1/demo-sessions/{session_id}/recover",
        headers=HEADERS,
        json={"reason_code": "stale_element"},
    )
    assert recover.status_code == 200, recover.text
    assert recover.json()["decision"] == "read_current_screen"

    end = api_client.post(
        f"/api/v1/demo-sessions/{session_id}/end",
        headers=HEADERS,
        json={"reason": "done"},
    )
    assert end.status_code == 200, end.text
    assert end.json()["session"]["status"] == "completed"

    resource_count = db_scalar(
        "select count(*) from session_resource_allocations where session_id = :session_id",
        {"session_id": session_id},
    )
    assert isinstance(resource_count, int)
    assert resource_count >= 4
