"""In-process session lock registry."""

import asyncio
from uuid import UUID


class SessionLockRegistry:
    def __init__(self) -> None:
        self._locks: dict[UUID, asyncio.Lock] = {}

    def lock_for(self, voice_session_id: UUID) -> asyncio.Lock:
        lock = self._locks.get(voice_session_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[voice_session_id] = lock
        return lock

    def discard(self, voice_session_id: UUID) -> None:
        self._locks.pop(voice_session_id, None)
