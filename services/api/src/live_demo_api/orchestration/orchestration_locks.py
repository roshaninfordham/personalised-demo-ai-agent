"""Session orchestration locking."""

from __future__ import annotations

import asyncio

from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.live_state.locks import acquire_lock, release_lock
from live_demo_api.live_state.redis_keys import session_lock_key
from live_demo_api.orchestration.orchestration_errors import OrchestrationLockError


class SessionOrchestrationLock:
    def __init__(self, redis: Redis[bytes], session_id: object, owner_id: str) -> None:
        self._redis = redis
        self._key = session_lock_key(str(session_id))
        self._owner_id = owner_id
        self._acquired = False

    async def __aenter__(self) -> SessionOrchestrationLock:
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._acquired:
            await self.release()

    async def acquire(self, *, wait_ms: int = 0, poll_ms: int = 25) -> None:
        ttl_ms = get_settings().session_orchestration_lock_ttl_ms
        deadline = asyncio.get_running_loop().time() + (wait_ms / 1000)
        while True:
            self._acquired = await acquire_lock(self._redis, self._key, self._owner_id, ttl_ms)
            if self._acquired:
                return
            if wait_ms <= 0 or asyncio.get_running_loop().time() >= deadline:
                raise OrchestrationLockError(
                    "Session orchestration lock is held.", code="session_locked"
                )
            await asyncio.sleep(poll_ms / 1000)

    async def release(self) -> bool:
        released = await release_lock(self._redis, self._key, self._owner_id)
        if released:
            self._acquired = False
        return released
