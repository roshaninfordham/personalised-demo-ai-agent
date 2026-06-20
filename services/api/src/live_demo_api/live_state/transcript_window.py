"""Focused transcript-window wrapper around LiveStateStore."""

from uuid import UUID

from live_demo_api.live_state.live_state_store import JsonObject, LiveStateStore


class TranscriptWindow:
    def __init__(self, store: LiveStateStore) -> None:
        self._store = store

    async def append(self, session_id: UUID | str, transcript: JsonObject) -> None:
        await self._store.append_transcript_window(session_id, transcript)

    async def get_recent(self, session_id: UUID | str) -> list[JsonObject]:
        return await self._store.get_transcript_window(session_id)
