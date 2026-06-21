from fastapi.testclient import TestClient

from services.api.tests.helpers import HEADERS, create_demo_session, create_product


def test_prewarm_session_transitions_created_to_waiting_for_user(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))

    response = api_client.post(
        f"/api/v1/demo-sessions/{session['session_id']}/prewarm", headers=HEADERS
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "waiting_for_user"
    assert body["runtime_state"] == "ready"
    assert body["readiness"]["browser_ready"] is True
    assert body["readiness"]["voice_ready"] is True
    assert body["readiness"]["learner_enqueued"] is True
