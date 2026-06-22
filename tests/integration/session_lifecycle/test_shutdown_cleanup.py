import pytest
from fastapi.testclient import TestClient
from services.api.tests.helpers import HEADERS, create_demo_session, create_product, db_scalar

pytestmark = pytest.mark.integration


def test_shutdown_cleanup_is_idempotent(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    session_id = str(session["session_id"])
    api_client.post(f"/api/v1/demo-sessions/{session_id}/prewarm", headers=HEADERS)

    first = api_client.post(
        f"/api/v1/demo-sessions/{session_id}/end",
        headers=HEADERS,
        json={"reason": "done"},
    )
    second = api_client.post(
        f"/api/v1/demo-sessions/{session_id}/end",
        headers=HEADERS,
        json={"reason": "done"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert (
        db_scalar(
            "select status from demo_sessions where session_id = cast(:session_id as uuid)",
            {"session_id": session_id},
        )
        == "completed"
    )
