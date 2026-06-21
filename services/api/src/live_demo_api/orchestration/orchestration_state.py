"""Runtime orchestration state stored compactly in Redis."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.live_state.redis_keys import orchestration_state_key
from live_demo_api.orchestration.orchestration_types import (
    ReadinessState,
    RecoveryState,
    SessionResource,
)


@dataclass(frozen=True, slots=True)
class OrchestrationState:
    organization_id: UUID
    session_id: UUID
    product_id: UUID
    status: str
    browser_session_id: UUID | None
    voice_session_id: UUID | None
    transport_session_id: str | None
    learner_run_id: UUID | None
    compiled_recipe_id: UUID | None
    readiness: ReadinessState
    recovery: RecoveryState | None
    resources: tuple[SessionResource, ...]
    updated_at: datetime


class OrchestrationStateStore:
    def __init__(self, redis: Redis[bytes], ttl_seconds: int | None = None) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds or get_settings().redis_session_ttl_seconds

    async def set_state(self, state: OrchestrationState) -> None:
        await self._redis.setex(
            orchestration_state_key(state.session_id),
            self._ttl_seconds,
            json.dumps(_jsonable(asdict(state)), sort_keys=True, separators=(",", ":")),
        )

    async def get_state(self, session_id: UUID) -> OrchestrationState | None:
        raw = await self._redis.get(orchestration_state_key(session_id))
        if raw is None:
            return None
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        data = cast(dict[str, Any], json.loads(text))
        return OrchestrationState(
            organization_id=UUID(str(data["organization_id"])),
            session_id=UUID(str(data["session_id"])),
            product_id=UUID(str(data["product_id"])),
            status=str(data["status"]),
            browser_session_id=_uuid_or_none(data.get("browser_session_id")),
            voice_session_id=_uuid_or_none(data.get("voice_session_id")),
            transport_session_id=(
                str(data["transport_session_id"]) if data.get("transport_session_id") else None
            ),
            learner_run_id=_uuid_or_none(data.get("learner_run_id")),
            compiled_recipe_id=_uuid_or_none(data.get("compiled_recipe_id")),
            readiness=ReadinessState(**cast(dict[str, Any], data["readiness"])),
            recovery=_recovery_from_data(data.get("recovery")),
            resources=tuple(SessionResource(**item) for item in data.get("resources", [])),
            updated_at=datetime.fromisoformat(str(data["updated_at"])),
        )


def _uuid_or_none(value: object) -> UUID | None:
    return UUID(str(value)) if value else None


def _recovery_from_data(value: object) -> RecoveryState | None:
    if not isinstance(value, dict):
        return None
    data = cast(dict[str, Any], value)
    return RecoveryState(
        session_id=UUID(str(data["session_id"])),
        active=bool(data["active"]),
        reason_code=str(data["reason_code"]),
        attempt_count=int(data["attempt_count"]),
        max_attempts=int(data["max_attempts"]),
        started_at=datetime.fromisoformat(str(data["started_at"])),
        last_attempt_at=(
            datetime.fromisoformat(str(data["last_attempt_at"]))
            if data.get("last_attempt_at")
            else None
        ),
        last_action=str(data["last_action"]) if data.get("last_action") else None,
        resolved=bool(data["resolved"]),
    )


def _jsonable(value: object) -> object:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return value
