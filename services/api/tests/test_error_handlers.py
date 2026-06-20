from fastapi.testclient import TestClient

from services.api.tests.helpers import HEADERS


def test_not_found_error_uses_standard_envelope(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/products/00000000-0000-4000-8000-000000000099",
        headers=HEADERS,
    )
    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "product_not_found"
    assert body["error"]["request_id"]


def test_validation_error_is_normalized(api_client: TestClient) -> None:
    response = api_client.post("/api/v1/products", headers=HEADERS, json={"product_name": "x"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"
