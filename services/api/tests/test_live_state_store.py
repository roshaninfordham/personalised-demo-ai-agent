from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.live_state.live_state_store import LiveStateDecodeError, LiveStateStore
from live_demo_api.live_state.redis_keys import session_state_key

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def redis_client() -> AsyncIterator[Redis[bytes]]:
    client = Redis.from_url(get_settings().redis_url)
    try:
        yield client
    finally:
        await client.close()


def _now() -> str:
    return datetime.now(UTC).isoformat()


async def test_live_state_round_trip(redis_client: Redis[bytes]) -> None:
    session_id = uuid4()
    organization_id = uuid4()
    product_id = uuid4()
    browser_session_id = uuid4()
    store = LiveStateStore(redis_client, ttl_seconds=60, transcript_max_entries=4)

    await store.set_session_state(
        session_id,
        {
            "session_id": str(session_id),
            "organization_id": str(organization_id),
            "product_id": str(product_id),
            "recipe_id": None,
            "status": "live",
            "current_phase": "overview",
            "user_persona": "founder",
            "updated_at": _now(),
        },
    )
    session_state = await store.get_session_state(session_id)
    assert session_state is not None
    assert session_state["status"] == "live"

    await store.set_current_screen(
        session_id,
        {
            "screen_id": str(uuid4()),
            "browser_session_id": str(browser_session_id),
            "url": "https://example.test",
            "title": "Example",
            "summary": "A visible screen.",
            "screen_hash": "abc123",
            "confidence": 0.9,
            "updated_at": _now(),
        },
    )
    current_screen = await store.get_current_screen(session_id)
    assert current_screen is not None
    assert current_screen["screen_hash"] == "abc123"

    await store.set_safe_actions(
        session_id,
        [
            {
                "action_id": "action-1",
                "action_type": "click_element",
                "label": "Open dashboard",
                "element_id": "el_1",
                "risk_level": "low",
                "score": 0.91,
                "expires_at": _now(),
            }
        ],
    )
    assert len(await store.get_safe_actions(session_id)) == 1

    for index in range(6):
        await store.append_transcript_window(
            session_id,
            {
                "transcript_event_id": str(uuid4()),
                "speaker": "user",
                "text": f"turn {index}",
                "created_at": _now(),
            },
        )
    window = await store.get_transcript_window(session_id)
    assert len(window) == 4
    assert window[0]["text"] == "turn 2"

    await store.set_browser_status(
        session_id,
        {
            "browser_session_id": str(browser_session_id),
            "status": "active",
            "current_url": "https://example.test",
            "current_screen_id": str(uuid4()),
            "last_action_id": None,
            "updated_at": _now(),
        },
    )
    browser_status = await store.get_browser_status(session_id)
    assert browser_status is not None
    assert browser_status["status"] == "active"


async def test_corrupt_session_state_raises(redis_client: Redis[bytes]) -> None:
    session_id = uuid4()
    await redis_client.set(session_state_key(session_id), "not-json")
    store = LiveStateStore(redis_client)
    with pytest.raises(LiveStateDecodeError):
        await store.get_session_state(session_id)
