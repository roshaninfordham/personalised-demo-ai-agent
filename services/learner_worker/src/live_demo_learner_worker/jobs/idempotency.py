"""Redis idempotency lock helpers."""

from __future__ import annotations

from uuid import UUID

from redis.asyncio import Redis


async def acquire_job_lock(redis: Redis[bytes], *, job_id: UUID, ttl_seconds: int) -> bool:
    result = await redis.set(f"live_demo:learner:job:{job_id}", "1", nx=True, ex=ttl_seconds)
    return bool(result)


async def release_job_lock(redis: Redis[bytes], *, job_id: UUID) -> None:
    await redis.delete(f"live_demo:learner:job:{job_id}")
