from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from live_demo_api.app import create_app

sys.path.append(str(Path(__file__).parent))


@pytest.fixture()
def api_client() -> Iterator[TestClient]:
    with TestClient(create_app()) as client:
        yield client
