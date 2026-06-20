from fastapi import FastAPI

from live_demo_api.app import create_app


def test_create_app_returns_fastapi_instance() -> None:
    app = create_app()
    assert isinstance(app, FastAPI)


def test_business_routers_are_registered() -> None:
    paths = set(create_app().openapi()["paths"])
    assert "/api/v1/products" in paths
    assert "/api/v1/demo-sessions" in paths
    assert "/api/v1/healthz" in paths
