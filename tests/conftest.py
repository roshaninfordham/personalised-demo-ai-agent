from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from live_demo_api.app import create_app


@pytest.fixture()
def api_client() -> Iterator[TestClient]:
    with TestClient(create_app()) as client:
        yield client
