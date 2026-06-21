"""Redis-backed orchestration idempotency helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any, cast
from uuid import UUID

from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.live_state.redis_keys import orchestration_idempotency_key


class IdempotencyStore:
    def __init__(self, redis: Redis[bytes]) -> None:
        self._redis = redis

    async def get(self, session_id: UUID, operation: str, key: str) -> dict[str, Any] | None:
        raw = await self._redis.get(
            orchestration_idempotency_key(session_id, operation, _safe_key(key))
        )
        if raw is None:
            return None
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return cast(dict[str, Any], json.loads(text))

    async def set(
        self,
        session_id: UUID,
        operation: str,
        key: str,
        value: dict[str, object],
    ) -> None:
        await self._redis.setex(
            orchestration_idempotency_key(session_id, operation, _safe_key(key)),
            get_settings().session_orchestration_idempotency_ttl_seconds,
            json.dumps(value, sort_keys=True, separators=(",", ":")),
        )


def derive_idempotency_key(operation: str, session_id: UUID, target_state: str) -> str:
    return _safe_key(f"{operation}:{session_id}:{target_state}")


def _safe_key(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:32]
