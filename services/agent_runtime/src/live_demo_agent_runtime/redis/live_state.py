"""Compact Redis live-state writer for voice status."""

from __future__ import annotations

import json
from collections.abc import Mapping

from redis.asyncio import Redis

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.redis.redis_keys import voice_status_key


class VoiceLiveStateWriter:
    def __init__(self, redis: Redis[str], settings: AgentRuntimeSettings) -> None:
        self._redis = redis
        self._settings = settings

    async def set_voice_status(self, demo_session_id: str, value: Mapping[str, object]) -> None:
        key = voice_status_key(self._settings.redis_key_prefix, demo_session_id)
        await self._redis.set(
            key,
            json.dumps(dict(value), sort_keys=True, separators=(",", ":")),
            ex=self._settings.redis_session_ttl_seconds,
        )
