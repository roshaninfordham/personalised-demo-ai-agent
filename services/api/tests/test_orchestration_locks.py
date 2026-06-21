from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.orchestration.orchestration_errors import OrchestrationLockError
from live_demo_api.orchestration.orchestration_locks import SessionOrchestrationLock

pytestmark = [pytest.mark.integration, pytest.mark.orchestration_integration]


@pytest_asyncio.fixture
async def redis_client() -> AsyncIterator[Redis[bytes]]:
    client = Redis.from_url(get_settings().redis_url)
    try:
        yield client
    finally:
        await client.close()


async def test_lock_release_only_works_for_owner(redis_client: Redis[bytes]) -> None:
    session_id = uuid4()
    lock = SessionOrchestrationLock(redis_client, session_id, "owner_1")

    await lock.acquire()
    wrong_owner = SessionOrchestrationLock(redis_client, session_id, "owner_2")

    assert await wrong_owner.release() is False
    assert await lock.release() is True


async def test_competing_lock_fails_safely(redis_client: Redis[bytes]) -> None:
    session_id = uuid4()
    first = SessionOrchestrationLock(redis_client, session_id, "owner_1")
    second = SessionOrchestrationLock(redis_client, session_id, "owner_2")

    await first.acquire()
    try:
        with pytest.raises(OrchestrationLockError):
            await second.acquire(wait_ms=50)
    finally:
        await first.release()
