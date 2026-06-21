"""Transcript sink coordinating publishing and optional database persistence."""

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from live_demo_agent_runtime.transcripts.transcript_buffer import (
    TranscriptBuffer,
    TranscriptWriteItem,
)
from live_demo_agent_runtime.transcripts.transcript_event_publisher import TranscriptEventPublisher
from live_demo_agent_runtime.transcripts.transcript_repository import TranscriptRepository


class TranscriptSink:
    def __init__(
        self,
        *,
        sessionmaker: async_sessionmaker[AsyncSession] | None,
        repository: TranscriptRepository,
        publisher: TranscriptEventPublisher,
    ) -> None:
        self._sessionmaker = sessionmaker
        self._repository = repository
        self._publisher = publisher

    async def enqueue(
        self,
        buffer: TranscriptBuffer,
        item: TranscriptWriteItem,
        *,
        trace_id: str,
    ) -> None:
        buffer.append(item)
        await self._publisher.publish_items([item], trace_id=trace_id)

    async def flush(self, buffer: TranscriptBuffer, *, trace_id: str = "") -> None:
        items = buffer.drain_batch()
        await self.flush_items(items, trace_id=trace_id, publish=False)

    async def flush_items(
        self,
        items: Sequence[TranscriptWriteItem],
        *,
        trace_id: str,
        publish: bool = True,
    ) -> None:
        if not items:
            return
        if publish:
            await self._publisher.publish_items(items, trace_id=trace_id)
        persist_items = [item for item in items if item.persist]
        if not persist_items or self._sessionmaker is None:
            return
        async with self._sessionmaker() as session:
            await self._repository.insert_transcript_events(session, persist_items)
            await session.commit()
