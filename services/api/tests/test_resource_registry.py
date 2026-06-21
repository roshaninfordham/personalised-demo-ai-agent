from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.api.tests.helpers import HEADERS, create_demo_session, create_product, db_scalar

pytestmark = [pytest.mark.integration, pytest.mark.orchestration_integration]


def test_duplicate_prewarm_prevents_duplicate_active_resource_allocations(
    api_client: TestClient,
) -> None:
    product = create_product(api_client)
    session = create_demo_session(api_client, str(product["product_id"]))
    session_id = str(session["session_id"])

    first = api_client.post(f"/api/v1/demo-sessions/{session_id}/prewarm", headers=HEADERS)
    second = api_client.post(f"/api/v1/demo-sessions/{session_id}/prewarm", headers=HEADERS)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    active_count = db_scalar(
        """
        select count(*)
        from session_resource_allocations
        where session_id = :session_id
        and status in ('allocating', 'allocated', 'ready', 'releasing')
        """,
        {"session_id": session_id},
    )
    distinct_count = db_scalar(
        """
        select count(distinct resource_type)
        from session_resource_allocations
        where session_id = :session_id
        and status in ('allocating', 'allocated', 'ready', 'releasing')
        """,
        {"session_id": session_id},
    )

    assert active_count == distinct_count
