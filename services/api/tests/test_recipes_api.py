from fastapi.testclient import TestClient

from services.api.tests.helpers import HEADERS, create_product, create_recipe, unique_name


def _recipe_payload(step_key: str = "overview") -> dict[str, object]:
    return {
        "recipe_name": unique_name("Recipe"),
        "target_persona": "founder",
        "demo_goal": "Show the overview screen.",
        "never_click": ["Delete", "Billing"],
        "steps": [
            {
                "step_order": 0,
                "step_key": step_key,
                "goal": "Show dashboard overview",
                "allowed_actions": ["highlight", "scroll"],
                "success_criteria": ["overview visible"],
            }
        ],
    }


def test_create_valid_recipe_succeeds(api_client: TestClient) -> None:
    product = create_product(api_client)
    response = api_client.post(
        f"/api/v1/products/{product['product_id']}/recipes",
        headers=HEADERS,
        json=_recipe_payload(),
    )
    assert response.status_code == 201, response.text
    assert response.json()["steps"][0]["step_order"] == 0


def test_create_invalid_recipe_fails(api_client: TestClient) -> None:
    product = create_product(api_client)
    payload = _recipe_payload()
    payload["steps"] = []
    response = api_client.post(
        f"/api/v1/products/{product['product_id']}/recipes",
        headers=HEADERS,
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {"request_validation_error", "invalid_demo_recipe"}


def test_validate_recipe_returns_structured_response(api_client: TestClient) -> None:
    product = create_product(api_client)
    recipe = create_recipe(api_client, str(product["product_id"]))
    response = api_client.post(
        f"/api/v1/products/{product['product_id']}/recipes/{recipe['recipe_id']}/validate",
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_blocked_allowed_action_fails(api_client: TestClient) -> None:
    product = create_product(api_client)
    payload = _recipe_payload()
    payload["steps"] = [
        {
            "step_order": 0,
            "step_key": "bad",
            "goal": "Bad step",
            "allowed_actions": ["delete account"],
        }
    ]
    response = api_client.post(
        f"/api/v1/products/{product['product_id']}/recipes",
        headers=HEADERS,
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_demo_recipe"


def test_activate_recipe_deactivates_previous_active_recipe(api_client: TestClient) -> None:
    product = create_product(api_client)
    product_id = str(product["product_id"])
    recipe_one = create_recipe(api_client, product_id)
    recipe_two_response = api_client.post(
        f"/api/v1/products/{product_id}/recipes",
        headers=HEADERS,
        json=_recipe_payload("deep_dive"),
    )
    assert recipe_two_response.status_code == 201, recipe_two_response.text
    recipe_two = recipe_two_response.json()

    first_activate = api_client.post(
        f"/api/v1/products/{product_id}/recipes/{recipe_one['recipe_id']}/activate",
        headers=HEADERS,
    )
    assert first_activate.status_code == 200
    second_activate = api_client.post(
        f"/api/v1/products/{product_id}/recipes/{recipe_two['recipe_id']}/activate",
        headers=HEADERS,
    )
    assert second_activate.status_code == 200
    assert second_activate.json()["recipe"]["is_active"] is True

    first_get = api_client.get(
        f"/api/v1/products/{product_id}/recipes/{recipe_one['recipe_id']}",
        headers=HEADERS,
    )
    assert first_get.status_code == 200
    assert first_get.json()["is_active"] is False


def test_archive_recipe_makes_inactive(api_client: TestClient) -> None:
    product = create_product(api_client)
    recipe = create_recipe(api_client, str(product["product_id"]))
    response = api_client.post(
        f"/api/v1/products/{product['product_id']}/recipes/{recipe['recipe_id']}/archive",
        headers=HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "archived"
    assert response.json()["is_active"] is False
