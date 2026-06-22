from __future__ import annotations

# mypy: ignore-errors
from time import perf_counter
from typing import Any

from locust import HttpUser, between, events, task

ORG_ID = "00000000-0000-0000-0000-000000000001"


class DemoSessionUser(HttpUser):
    wait_time = between(1, 3)

    product_id: str | None = None
    session_id: str | None = None

    def on_start(self) -> None:
        self.product_id = self._create_product()
        self.session_id = self._create_session(self.product_id)

    @task
    def run_demo_flow(self) -> None:
        if self.session_id is None:
            return
        self._timed_post(
            name="prewarm_session",
            url=f"/api/v1/demo-sessions/{self.session_id}/prewarm",
            max_latency_ms=10000,
        )
        self._timed_post(
            name="start_session",
            url=f"/api/v1/demo-sessions/{self.session_id}/start",
            max_latency_ms=1500,
        )
        self.client.get(
            f"/api/v1/demo-sessions/{self.session_id}/orchestration-state",
            headers=_headers(),
            name="get_session_state",
        )
        self._timed_post(
            name="end_session",
            url=f"/api/v1/demo-sessions/{self.session_id}/end",
            max_latency_ms=15000,
        )
        self.session_id = self._create_session(self.product_id)

    def _create_product(self) -> str | None:
        response = self.client.post(
            "/api/v1/products",
            json={
                "product_name": f"Load Product {id(self)}",
                "product_url": "https://example.com",
                "default_persona": "founder",
            },
            headers=_headers(),
            name="create_product",
            catch_response=True,
        )
        with response:
            if response.status_code >= 500:
                response.failure("product creation returned server error")
                return None
            data = _json(response.json())
            return _optional_str(data.get("product_id"))

    def _create_session(self, product_id: str | None) -> str | None:
        if product_id is None:
            return None
        response = self.client.post(
            "/api/v1/demo-sessions",
            json={
                "product_id": product_id,
                "start_url": "https://example.com",
                "user_persona": "founder",
            },
            headers=_headers(),
            name="create_session",
            catch_response=True,
        )
        with response:
            if response.status_code >= 500:
                response.failure("session creation returned server error")
                return None
            data = _json(response.json())
            return _optional_str(data.get("session_id"))

    def _timed_post(self, *, name: str, url: str, max_latency_ms: float) -> None:
        started = perf_counter()
        response = self.client.post(url, headers=_headers(), name=name, catch_response=True)
        latency_ms = (perf_counter() - started) * 1000
        events.request.fire(
            request_type="CUSTOM",
            name=f"{name}_latency",
            response_time=latency_ms,
            response_length=0,
            exception=None if latency_ms <= max_latency_ms else TimeoutError(name),
            context={},
        )
        with response:
            if response.status_code >= 500:
                response.failure(f"{name} returned server error")


def _headers() -> dict[str, str]:
    return {"Content-Type": "application/json", "X-Organization-ID": ORG_ID}


def _json(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
