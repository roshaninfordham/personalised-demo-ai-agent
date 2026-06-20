"""Event outbox repository."""

from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import EventOutbox
from live_demo_api.db.types import EventOutboxStatus
from live_demo_contracts.event import EventEnvelope


class EventOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_event(self, event: EventEnvelope) -> EventOutbox:
        row = EventOutbox(
            organization_id=UUID(event.organization_id)
            if event.organization_id is not None
            else None,
            session_id=UUID(event.session_id) if event.session_id is not None else None,
            event_id=UUID(event.event_id),
            event_type=str(event.event_type),
            payload=event.payload,
            trace_id=event.trace_id,
            status=EventOutboxStatus.PENDING.value,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_pending(self, *, limit: int = 100) -> list[EventOutbox]:
        statement = (
            select(EventOutbox)
            .where(
                EventOutbox.status == EventOutboxStatus.PENDING.value,
                EventOutbox.available_at <= sa.func.now(),
            )
            .order_by(EventOutbox.available_at.asc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())

    async def mark_published(self, outbox_id: UUID) -> None:
        row = await self._session.get(EventOutbox, outbox_id)
        if row is None:
            return
        row.status = EventOutboxStatus.PUBLISHED.value
        row.published_at = datetime.now(UTC)
