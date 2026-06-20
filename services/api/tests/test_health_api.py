from fastapi.testclient import TestClient


def test_healthz_works_without_dependency_checks(api_client: TestClient) -> None:
    response = api_client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"]


def test_readyz_checks_dependencies(api_client: TestClient) -> None:
    response = api_client.get("/readyz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "ok"
