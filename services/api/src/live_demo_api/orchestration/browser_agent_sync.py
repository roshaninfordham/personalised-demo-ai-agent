"""Browser-agent synchronization state and deterministic scheduling."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal, cast
from uuid import UUID

from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.live_state.redis_keys import sync_state_key
from live_demo_api.orchestration.orchestration_types import utc_now


@dataclass(frozen=True, slots=True)
class BrowserAgentSyncState:
    session_id: UUID
    active_turn_id: UUID | None
    pending_action_id: str | None
    pending_command_id: UUID | None
    speech_state: Literal["idle", "speaking", "interrupted"]
    browser_action_state: Literal["idle", "queued", "started", "completed", "failed"]
    screen_update_state: Literal["not_waiting", "waiting", "updated", "timeout"]
    updated_at: datetime


class BrowserAgentSynchronizer:
    def __init__(self, redis: Redis[bytes]) -> None:
        self._redis = redis

    async def get_state(self, session_id: UUID) -> BrowserAgentSyncState:
        raw = await self._redis.get(sync_state_key(session_id))
        if raw is None:
            return BrowserAgentSyncState(
                session_id=session_id,
                active_turn_id=None,
                pending_action_id=None,
                pending_command_id=None,
                speech_state="idle",
                browser_action_state="idle",
                screen_update_state="not_waiting",
                updated_at=utc_now(),
            )
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        data = cast(dict[str, object], json.loads(text))
        return BrowserAgentSyncState(
            session_id=UUID(str(data["session_id"])),
            active_turn_id=(
                UUID(str(data["active_turn_id"])) if data.get("active_turn_id") else None
            ),
            pending_action_id=(
                str(data["pending_action_id"]) if data.get("pending_action_id") else None
            ),
            pending_command_id=(
                UUID(str(data["pending_command_id"])) if data.get("pending_command_id") else None
            ),
            speech_state=cast(Literal["idle", "speaking", "interrupted"], data["speech_state"]),
            browser_action_state=cast(
                Literal["idle", "queued", "started", "completed", "failed"],
                data["browser_action_state"],
            ),
            screen_update_state=cast(
                Literal["not_waiting", "waiting", "updated", "timeout"],
                data["screen_update_state"],
            ),
            updated_at=datetime.fromisoformat(str(data["updated_at"])),
        )

    async def set_state(self, state: BrowserAgentSyncState) -> None:
        payload = asdict(state)
        for key, value in tuple(payload.items()):
            if isinstance(value, UUID):
                payload[key] = str(value)
            elif isinstance(value, datetime):
                payload[key] = value.isoformat()
        await self._redis.setex(
            sync_state_key(state.session_id),
            get_settings().redis_session_ttl_seconds,
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
        )

    async def queue_action(
        self, *, session_id: UUID, turn_id: UUID, action_id: str, command_id: UUID
    ) -> BrowserAgentSyncState:
        current = await self.get_state(session_id)
        if current.pending_action_id and current.browser_action_state in {"queued", "started"}:
            raise ValueError("action_already_pending")
        state = BrowserAgentSyncState(
            session_id=session_id,
            active_turn_id=turn_id,
            pending_action_id=action_id,
            pending_command_id=command_id,
            speech_state="speaking" if get_settings().sync_speech_before_action else "idle",
            browser_action_state="queued",
            screen_update_state="not_waiting",
            updated_at=utc_now(),
        )
        await self.set_state(state)
        return state

    async def mark_started(self, session_id: UUID) -> BrowserAgentSyncState:
        current = await self.get_state(session_id)
        state = BrowserAgentSyncState(
            **{**asdict(current), "browser_action_state": "started", "updated_at": utc_now()}
        )
        await self.set_state(state)
        return state

    async def mark_screen_updated(self, session_id: UUID) -> BrowserAgentSyncState:
        current = await self.get_state(session_id)
        state = BrowserAgentSyncState(
            **{
                **asdict(current),
                "browser_action_state": "completed",
                "screen_update_state": "updated",
                "pending_action_id": None,
                "pending_command_id": None,
                "updated_at": utc_now(),
            }
        )
        await self.set_state(state)
        return state

    async def mark_interrupted(self, session_id: UUID) -> BrowserAgentSyncState:
        current = await self.get_state(session_id)
        state = BrowserAgentSyncState(
            **{
                **asdict(current),
                "speech_state": "interrupted",
                "browser_action_state": "idle"
                if current.browser_action_state == "queued"
                else current.browser_action_state,
                "pending_action_id": None
                if current.browser_action_state == "queued"
                else current.pending_action_id,
                "updated_at": utc_now(),
            }
        )
        await self.set_state(state)
        return state
