from fastapi.testclient import TestClient

from services.api.tests.helpers import HEADERS, create_product


def test_create_list_update_delete_guidance(api_client: TestClient) -> None:
    product = create_product(api_client)
    product_id = product["product_id"]

    create_response = api_client.post(
        f"/api/v1/products/{product_id}/guidance",
        headers=HEADERS,
        json={
            "guidance_type": "product_positioning",
            "title": "Founder positioning",
            "content": {"summary": "Focus on speed to insight."},
        },
    )
    assert create_response.status_code == 201, create_response.text
    guidance = create_response.json()

    list_response = api_client.get(
        f"/api/v1/products/{product_id}/guidance?guidance_type=product_positioning",
        headers=HEADERS,
    )
    assert list_response.status_code == 200
    assert any(
        item["guidance_id"] == guidance["guidance_id"] for item in list_response.json()["items"]
    )

    patch_response = api_client.patch(
        f"/api/v1/products/{product_id}/guidance/{guidance['guidance_id']}",
        headers=HEADERS,
        json={"title": "Updated guidance"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Updated guidance"

    delete_response = api_client.delete(
        f"/api/v1/products/{product_id}/guidance/{guidance['guidance_id']}",
        headers=HEADERS,
    )
    assert delete_response.status_code == 204


def test_guidance_rejects_secret_keys(api_client: TestClient) -> None:
    product = create_product(api_client)
    response = api_client.post(
        f"/api/v1/products/{product['product_id']}/guidance",
        headers=HEADERS,
        json={
            "guidance_type": "text",
            "content": {"api_key": "do-not-store"},
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "guidance_contains_secret"


def test_guidance_rejects_overly_deep_json(api_client: TestClient) -> None:
    product = create_product(api_client)
    deep: dict[str, object] = {"value": "x"}
    for _ in range(12):
        deep = {"nested": deep}
    response = api_client.post(
        f"/api/v1/products/{product['product_id']}/guidance",
        headers=HEADERS,
        json={"guidance_type": "text", "content": deep},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "guidance_too_large_or_deep"


def test_forbidden_actions_guidance_requires_string_list(api_client: TestClient) -> None:
    product = create_product(api_client)
    response = api_client.post(
        f"/api/v1/products/{product['product_id']}/guidance",
        headers=HEADERS,
        json={"guidance_type": "forbidden_actions", "content": {"never_click": ["Delete", 123]}},
    )
    assert response.status_code == 422
