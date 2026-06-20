"""Typed Redis live-state accessors."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from uuid import UUID

from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.live_state.redis_keys import (
    browser_status_key,
    current_screen_key,
    safe_actions_key,
    session_state_key,
    transcript_window_key,
)

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


class LiveStateDecodeError(ValueError):
    """Raised when Redis contains malformed live-state data."""


def _to_json(value: Mapping[str, JsonValue] | Sequence[JsonObject]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _from_json_object(raw: bytes | str | None, required_fields: set[str]) -> JsonObject | None:
    if raw is None:
        return None
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LiveStateDecodeError("Redis value is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise LiveStateDecodeError("Redis value must be a JSON object")
    missing = required_fields.difference(parsed)
    if missing:
        raise LiveStateDecodeError(f"Redis value is missing fields: {sorted(missing)}")
    return parsed


def _from_json_list(values: Sequence[bytes | str]) -> list[JsonObject]:
    decoded: list[JsonObject] = []
    for value in values:
        parsed = _from_json_object(value, set())
        if parsed is None:
            raise LiveStateDecodeError("Redis list entry decoded to None")
        decoded.append(parsed)
    return decoded


class LiveStateStore:
    def __init__(
        self,
        redis: Redis[bytes],
        *,
        ttl_seconds: int | None = None,
        transcript_max_entries: int | None = None,
    ) -> None:
        settings = get_settings()
        self._redis = redis
        self._ttl_seconds = ttl_seconds or settings.redis_session_ttl_seconds
        self._transcript_max_entries = (
            transcript_max_entries or settings.redis_transcript_window_max_entries
        )

    async def set_session_state(self, session_id: UUID | str, state: JsonObject) -> None:
        await self._redis.setex(session_state_key(session_id), self._ttl_seconds, _to_json(state))

    async def get_session_state(self, session_id: UUID | str) -> JsonObject | None:
        return _from_json_object(
            await self._redis.get(session_state_key(session_id)),
            {
                "session_id",
                "organization_id",
                "product_id",
                "status",
                "current_phase",
                "updated_at",
            },
        )

    async def patch_session_state(self, session_id: UUID | str, patch: JsonObject) -> JsonObject:
        current = await self.get_session_state(session_id)
        if current is None:
            raise LiveStateDecodeError("Cannot patch missing session state")
        current.update(patch)
        await self.set_session_state(session_id, current)
        return current

    async def delete_session_state(self, session_id: UUID | str) -> None:
        await self._redis.delete(session_state_key(session_id))

    async def set_current_screen(self, session_id: UUID | str, screen: JsonObject) -> None:
        await self._redis.setex(current_screen_key(session_id), self._ttl_seconds, _to_json(screen))

    async def get_current_screen(self, session_id: UUID | str) -> JsonObject | None:
        return _from_json_object(
            await self._redis.get(current_screen_key(session_id)),
            {"screen_id", "browser_session_id", "url", "screen_hash", "confidence", "updated_at"},
        )

    async def set_safe_actions(self, session_id: UUID | str, actions: Sequence[JsonObject]) -> None:
        if len(actions) > 20:
            raise ValueError("safe actions cannot exceed 20 entries")
        await self._redis.setex(safe_actions_key(session_id), self._ttl_seconds, _to_json(actions))

    async def get_safe_actions(self, session_id: UUID | str) -> list[JsonObject]:
        raw = await self._redis.get(safe_actions_key(session_id))
        if raw is None:
            return []
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LiveStateDecodeError("safe actions value is not valid JSON") from exc
        if not isinstance(parsed, list) or any(not isinstance(item, dict) for item in parsed):
            raise LiveStateDecodeError("safe actions value must be a list of objects")
        return parsed

    async def append_transcript_window(
        self, session_id: UUID | str, transcript: JsonObject
    ) -> None:
        key = transcript_window_key(session_id)
        await self._redis.rpush(key, _to_json(transcript))
        await self._redis.ltrim(key, -self._transcript_max_entries, -1)
        await self._redis.expire(key, self._ttl_seconds)

    async def get_transcript_window(self, session_id: UUID | str) -> list[JsonObject]:
        raw_values = await self._redis.lrange(transcript_window_key(session_id), 0, -1)
        return _from_json_list(raw_values)

    async def set_browser_status(self, session_id: UUID | str, status: JsonObject) -> None:
        await self._redis.setex(browser_status_key(session_id), self._ttl_seconds, _to_json(status))

    async def get_browser_status(self, session_id: UUID | str) -> JsonObject | None:
        return _from_json_object(
            await self._redis.get(browser_status_key(session_id)),
            {"browser_session_id", "status", "current_url", "updated_at"},
        )
