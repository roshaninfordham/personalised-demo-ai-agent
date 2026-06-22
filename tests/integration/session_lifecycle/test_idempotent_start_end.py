import pytest
from fastapi.testclient import TestClient
from services.api.tests.helpers import HEADERS, create_demo_session, create_product

pytestmark = pytest.mark.integration


def test_duplicate_start_returns_existing_join_config(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    session_id = str(session["session_id"])
    api_client.post(f"/api/v1/demo-sessions/{session_id}/prewarm", headers=HEADERS)

    first = api_client.post(f"/api/v1/demo-sessions/{session_id}/start", headers=HEADERS, json={})
    second = api_client.post(f"/api/v1/demo-sessions/{session_id}/start", headers=HEADERS, json={})

    assert first.status_code == 200
    assert second.status_code == 200
    first_join = dict(first.json()["join_config"])
    second_join = dict(second.json()["join_config"])
    assert first_join.pop("expires_at", None)
    assert second_join.pop("expires_at", None)
    assert first_join == second_join
