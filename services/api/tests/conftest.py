from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from live_demo_api.app import create_app
from live_demo_api.config import get_settings

sys.path.append(str(Path(__file__).parent))


@pytest.fixture()
def api_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("BROWSER_RUNTIME_ENABLE_MOCK_FALLBACK", "true")
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:
            yield client
    finally:
        get_settings.cache_clear()
