import pytest
from fastapi.testclient import TestClient
from services.api.tests.helpers import HEADERS, create_demo_session, create_product

pytestmark = pytest.mark.integration


def test_recovery_flow_returns_safe_read_current_screen(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    session_id = str(session["session_id"])
    api_client.post(f"/api/v1/demo-sessions/{session_id}/prewarm", headers=HEADERS)

    response = api_client.post(
        f"/api/v1/demo-sessions/{session_id}/recover",
        headers=HEADERS,
        json={"reason_code": "stale_element"},
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "read_current_screen"
