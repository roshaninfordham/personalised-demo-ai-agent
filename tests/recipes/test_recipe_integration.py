from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient

from live_demo_api.app import create_app
from live_demo_api.config import get_settings

FIXTURES = Path(__file__).parent / "fixtures"
HEADERS = {
    "X-Organization-ID": "00000000-0000-0000-0000-000000000001",
    "X-User-ID": "00000000-0000-0000-0000-000000000002",
    "X-User-Role": "owner",
}


@pytest.fixture()
def api_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("OBJECT_STORAGE_AUTO_CREATE_BUCKET", "false")
    get_settings.cache_clear()
    with TestClient(create_app()) as client:
        yield client
    get_settings.cache_clear()


def create_product(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/products",
        headers=HEADERS,
        json={
            "product_name": "Recipe Test Product",
            "product_url": "https://example.com",
            "default_persona": "founder",
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, object], response.json())


def create_recipe(client: TestClient, product_id: str) -> dict[str, object]:
    payload = json.loads((FIXTURES / "valid_minimal_recipe.json").read_text())
    response = client.post(
        f"/api/v1/products/{product_id}/recipes",
        headers=HEADERS,
        json=payload,
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, object], response.json())


def create_demo_session(
    client: TestClient, product_id: str, recipe_id: str | None = None
) -> dict[str, object]:
    payload: dict[str, object] = {
        "product_id": product_id,
        "user_persona": "founder",
        "user_company": "Example Co",
        "user_display_name": "Jane",
        "user_email": "jane@example.com",
    }
    if recipe_id is not None:
        payload["recipe_id"] = recipe_id
    response = client.post("/api/v1/demo-sessions", headers=HEADERS, json=payload)
    assert response.status_code == 201, response.text
    body = cast(dict[str, object], response.json())
    return cast(dict[str, object], body["session"])


@pytest.mark.integration
def test_raw_recipe_validate_generate_compile_and_progress(api_client: TestClient) -> None:
    product = create_product(api_client)
    product_id = str(product["product_id"])
    payload = json.loads((FIXTURES / "valid_full_recipe.json").read_text())

    validate = api_client.post(
        f"/api/v1/products/{product_id}/recipes/validate",
        headers=HEADERS,
        json=payload,
    )
    assert validate.status_code == 200, validate.text
    assert validate.json()["valid"] is True

    generate = api_client.post(
        f"/api/v1/products/{product_id}/recipes/generate",
        headers=HEADERS,
        json={
            "target_persona": "founder",
            "text_guidance": (
                "Show dashboard first, then metric creation. Avoid billing and delete."
            ),
        },
    )
    assert generate.status_code == 200, generate.text
    assert generate.json()["status"] == "draft"
    assert generate.json()["recipe_id"] is not None

    recipe = create_recipe(api_client, product_id)
    compile_response = api_client.post(
        f"/api/v1/products/{product_id}/recipes/{recipe['recipe_id']}/compile",
        headers=HEADERS,
    )
    assert compile_response.status_code == 200, compile_response.text
    assert compile_response.json()["compiled_hash"]

    compiled_get = api_client.get(
        f"/api/v1/products/{product_id}/recipes/{recipe['recipe_id']}/compiled",
        headers=HEADERS,
    )
    assert compiled_get.status_code == 200, compiled_get.text
    assert compiled_get.json()["recipe_hash"] == compile_response.json()["recipe_hash"]

    session = create_demo_session(api_client, product_id, str(recipe["recipe_id"]))
    progress = api_client.get(
        f"/api/v1/demo-sessions/{session['session_id']}/recipe-progress",
        headers=HEADERS,
    )
    assert progress.status_code == 200, progress.text
    assert progress.json()["total_count"] >= 1

    skip = api_client.post(
        f"/api/v1/demo-sessions/{session['session_id']}/recipe-progress/overview/skip",
        headers=HEADERS,
    )
    assert skip.status_code == 200, skip.text
    assert skip.json()["steps"][0]["status"] == "skipped"
