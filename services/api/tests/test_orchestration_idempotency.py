from uuid import uuid4

from live_demo_api.orchestration.idempotency import IdempotencyStore, derive_idempotency_key
from services.api.tests.test_browser_agent_sync import MemoryRedis


async def test_idempotency_store_replays_stored_result() -> None:
    redis = MemoryRedis()
    store = IdempotencyStore(redis)  # type: ignore[arg-type]
    session_id = uuid4()

    await store.set(session_id, "start", "key_1", {"status": "waiting_for_user"})

    assert await store.get(session_id, "start", "key_1") == {"status": "waiting_for_user"}


def test_derive_idempotency_key_is_deterministic() -> None:
    session_id = uuid4()

    assert derive_idempotency_key("start", session_id, "live") == derive_idempotency_key(
        "start", session_id, "live"
    )
