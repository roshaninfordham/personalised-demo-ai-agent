"""Bounded transcript write buffer with partial-drop backpressure."""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

TranscriptSpeaker = Literal["user", "assistant", "system", "tool"]
TranscriptChunkType = Literal["partial", "final", "interrupted"]


@dataclass(frozen=True, slots=True)
class TranscriptWriteItem:
    transcript_event_id: UUID
    organization_id: UUID
    demo_session_id: UUID
    speaker: TranscriptSpeaker
    chunk_type: TranscriptChunkType
    text: str
    is_final: bool
    start_ms: int | None
    end_ms: int | None
    confidence: float | None
    turn_id: UUID | None
    created_at: datetime
    persist: bool
    publish: bool


class TranscriptBuffer:
    def __init__(self, max_items: int = 256) -> None:
        self._max_items = max_items
        self._items: deque[TranscriptWriteItem] = deque()
        self._latest_partial_by_turn: dict[UUID, TranscriptWriteItem] = {}
        self.partial_dropped_count = 0

    def append(self, item: TranscriptWriteItem) -> None:
        if item.chunk_type == "partial" and item.turn_id is not None:
            self._latest_partial_by_turn[item.turn_id] = item
        self._items.append(item)
        self._enforce_capacity()

    def _enforce_capacity(self) -> None:
        while len(self._items) > self._max_items:
            dropped = self._drop_oldest_partial()
            if not dropped:
                return

    def _drop_oldest_partial(self) -> bool:
        for index, item in enumerate(self._items):
            if item.chunk_type == "partial":
                del self._items[index]
                latest_partial = (
                    self._latest_partial_by_turn.get(item.turn_id)
                    if item.turn_id is not None
                    else None
                )
                if item.turn_id is not None and latest_partial == item:
                    self._latest_partial_by_turn.pop(item.turn_id, None)
                self.partial_dropped_count += 1
                return True
        return False

    def drain_batch(self, max_items: int | None = None) -> list[TranscriptWriteItem]:
        if max_items is None:
            max_items = len(self._items)
        batch: list[TranscriptWriteItem] = []
        while self._items and len(batch) < max_items:
            item = self._items.popleft()
            if item.turn_id is not None and self._latest_partial_by_turn.get(item.turn_id) == item:
                self._latest_partial_by_turn.pop(item.turn_id, None)
            batch.append(item)
        return batch

    def snapshot(self) -> Sequence[TranscriptWriteItem]:
        return tuple(self._items)

    @property
    def length(self) -> int:
        return len(self._items)
