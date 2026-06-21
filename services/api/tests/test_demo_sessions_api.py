from fastapi.testclient import TestClient

from services.api.tests.helpers import HEADERS, create_demo_session, create_product, create_recipe


def test_create_session_succeeds(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    assert session["status"] == "created"
    assert session["product_id"] == product["product_id"]


def test_create_session_validates_product_ownership(api_client: TestClient) -> None:
    product = create_product(api_client)
    response = api_client.post(
        "/api/v1/demo-sessions",
        headers={**HEADERS, "X-Organization-ID": "00000000-0000-0000-0000-000000000099"},
        json={"product_id": product["product_id"]},
    )
    assert response.status_code == 404


def test_create_session_validates_recipe_ownership(api_client: TestClient) -> None:
    product_one = create_product(api_client)
    recipe = create_recipe(api_client, str(product_one["product_id"]))
    product_two = create_product(api_client)
    response = api_client.post(
        "/api/v1/demo-sessions",
        headers=HEADERS,
        json={"product_id": product_two["product_id"], "recipe_id": recipe["recipe_id"]},
    )
    assert response.status_code == 404


def test_start_session_transitions_to_prewarming_and_is_idempotent(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))

    first = api_client.post(
        f"/api/v1/demo-sessions/{session['session_id']}/start",
        headers=HEADERS,
        json={},
    )
    assert first.status_code == 200, first.text
    assert first.json()["session"]["status"] == "waiting_for_user"
    assert first.json()["join_config"]["status"] == "not_implemented_in_phase_3"
    assert first.json()["join_config"]["join_token"] is None

    second = api_client.post(
        f"/api/v1/demo-sessions/{session['session_id']}/start",
        headers=HEADERS,
        json={},
    )
    assert second.status_code == 200
    assert second.json()["session"]["status"] == "waiting_for_user"


def test_end_session_transitions_to_completed(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    response = api_client.post(
        f"/api/v1/demo-sessions/{session['session_id']}/end",
        headers=HEADERS,
        json={"reason": "done"},
    )
    assert response.status_code == 200
    assert response.json()["session"]["status"] == "completed"


def test_invalid_transition_returns_409(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    end_response = api_client.post(
        f"/api/v1/demo-sessions/{session['session_id']}/end",
        headers=HEADERS,
        json={},
    )
    assert end_response.status_code == 200

    start_response = api_client.post(
        f"/api/v1/demo-sessions/{session['session_id']}/start",
        headers=HEADERS,
        json={},
    )
    assert start_response.status_code == 409


def test_get_session_state_merges_db_and_redis_state(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    api_client.post(
        f"/api/v1/demo-sessions/{session['session_id']}/start", headers=HEADERS, json={}
    )

    response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/state", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["session"]["status"] == "waiting_for_user"
    assert body["live_state"]["available"] is True
    assert len(body["live_state"]["safe_actions"]) >= 1


def test_list_sessions_and_join_config(api_client: TestClient) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))

    list_response = api_client.get("/api/v1/demo-sessions?limit=1", headers=HEADERS)
    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) == 1

    join_response = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/join-config",
        headers=HEADERS,
    )
    assert join_response.status_code == 200
    assert join_response.json()["join_token"] is None
