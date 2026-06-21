"""Append-only session lifecycle event repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import SessionLifecycleEvent


class SessionLifecycleEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        event_type: str,
        trace_id: str,
        previous_status: str | None = None,
        next_status: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        severity: str = "info",
        message: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> SessionLifecycleEvent:
        row = SessionLifecycleEvent(
            organization_id=organization_id,
            session_id=session_id,
            event_type=event_type,
            previous_status=previous_status,
            next_status=next_status,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=severity,
            message=message,
            metadata_json=metadata or {},
            trace_id=trace_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row
