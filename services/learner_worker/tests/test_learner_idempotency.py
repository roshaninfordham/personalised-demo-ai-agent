from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

import pytest

from live_demo_learner_worker.jobs.idempotency import acquire_job_lock, release_job_lock


class FakeRedis:
    def __init__(self) -> None:
        self.items: set[str] = set()

    async def set(self, key: str, value: str, *, nx: bool, ex: int) -> bool:
        _ = (value, ex)
        if nx and key in self.items:
            return False
        self.items.add(key)
        return True

    async def delete(self, key: str) -> int:
        self.items.discard(key)
        return 1


@pytest.mark.asyncio
async def test_job_lock_dedupes() -> None:
    redis = cast(Any, FakeRedis())
    job_id = uuid4()

    assert await acquire_job_lock(redis, job_id=job_id, ttl_seconds=10)
    assert not await acquire_job_lock(redis, job_id=job_id, ttl_seconds=10)
    await release_job_lock(redis, job_id=job_id)
    assert await acquire_job_lock(redis, job_id=job_id, ttl_seconds=10)
