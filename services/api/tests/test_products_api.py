from fastapi.testclient import TestClient

from services.api.tests.helpers import HEADERS, create_product, db_scalar, unique_name


def test_create_product_succeeds(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/products",
        headers=HEADERS,
        json={
            "product_name": unique_name("Analytics"),
            "product_url": "https://Example.com/path#fragment",
            "default_persona": "founder",
            "configuration": {"allowed_domains": ["example.com"]},
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["product_url"] == "https://example.com/path"
    assert body["configuration"]["allowed_domains"] == ["example.com"]


def test_create_product_rejects_invalid_url(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/products",
        headers=HEADERS,
        json={"product_name": "Bad URL", "product_url": "javascript:alert(1)"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_product_url"


def test_create_product_rejects_local_url_by_default(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/products",
        headers=HEADERS,
        json={"product_name": "Local URL", "product_url": "http://localhost:3000"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "blocked_product_url"


def test_get_list_update_delete_product(api_client: TestClient) -> None:
    product = create_product(api_client)
    product_id = product["product_id"]

    get_response = api_client.get(f"/api/v1/products/{product_id}", headers=HEADERS)
    assert get_response.status_code == 200
    assert get_response.json()["product_id"] == product_id

    list_response = api_client.get("/api/v1/products?limit=1", headers=HEADERS)
    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) == 1

    patch_response = api_client.patch(
        f"/api/v1/products/{product_id}",
        headers=HEADERS,
        json={"product_summary": "Updated summary."},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["product_summary"] == "Updated summary."

    delete_response = api_client.delete(f"/api/v1/products/{product_id}", headers=HEADERS)
    assert delete_response.status_code == 204

    missing_response = api_client.get(f"/api/v1/products/{product_id}", headers=HEADERS)
    assert missing_response.status_code == 404


def test_cross_tenant_get_returns_404(api_client: TestClient) -> None:
    product = create_product(api_client)
    response = api_client.get(
        f"/api/v1/products/{product['product_id']}",
        headers={**HEADERS, "X-Organization-ID": "00000000-0000-0000-0000-000000000099"},
    )
    assert response.status_code == 404


def test_product_mutation_writes_audit_log(api_client: TestClient) -> None:
    product = create_product(api_client)
    count = db_scalar(
        """
        select count(*)
        from audit_logs
        where action = 'product.create'
        and resource_id = :product_id
        """,
        {"product_id": product["product_id"]},
    )
    assert count == 1
