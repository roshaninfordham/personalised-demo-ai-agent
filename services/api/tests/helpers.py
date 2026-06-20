from __future__ import annotations

from typing import cast
from uuid import uuid4

import sqlalchemy as sa
from fastapi.testclient import TestClient

from live_demo_api.config import get_settings

ORG_ID = "00000000-0000-0000-0000-000000000001"
USER_ID = "00000000-0000-0000-0000-000000000002"
HEADERS = {
    "X-Organization-ID": ORG_ID,
    "X-User-ID": USER_ID,
    "X-User-Role": "owner",
}


def unique_name(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def create_product(
    client: TestClient, *, product_url: str = "https://example.com"
) -> dict[str, object]:
    response = client.post(
        "/api/v1/products",
        headers=HEADERS,
        json={
            "product_name": unique_name("Product"),
            "product_url": product_url,
            "default_persona": "founder",
        },
    )
    assert response.status_code == 201, response.text
    return cast(dict[str, object], response.json())


def create_recipe(client: TestClient, product_id: str) -> dict[str, object]:
    response = client.post(
        f"/api/v1/products/{product_id}/recipes",
        headers=HEADERS,
        json={
            "recipe_name": unique_name("Recipe"),
            "target_persona": "founder",
            "demo_goal": "Show the overview screen.",
            "never_click": ["Delete", "Billing"],
            "steps": [
                {
                    "step_order": 0,
                    "step_key": "overview",
                    "goal": "Show dashboard overview",
                    "allowed_actions": ["highlight", "scroll"],
                    "success_criteria": ["overview visible"],
                }
            ],
        },
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
    return cast(dict[str, object], response.json()["session"])


def db_execute(statement: str, parameters: dict[str, object] | None = None) -> None:
    engine = sa.create_engine(get_settings().database_sync_url)
    try:
        with engine.begin() as connection:
            connection.execute(sa.text(statement), parameters or {})
    finally:
        engine.dispose()


def db_scalar(statement: str, parameters: dict[str, object] | None = None) -> object:
    engine = sa.create_engine(get_settings().database_sync_url)
    try:
        with engine.connect() as connection:
            return connection.execute(sa.text(statement), parameters or {}).scalar()
    finally:
        engine.dispose()
