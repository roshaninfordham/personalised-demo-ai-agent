from fastapi.testclient import TestClient

from live_demo_agent_runtime.app import create_app


def test_app_health_endpoint_without_lifespan_db_connection() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
