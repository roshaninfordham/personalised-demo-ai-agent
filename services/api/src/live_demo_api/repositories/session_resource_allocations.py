"""Repository for session resource allocations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import SessionResourceAllocation

ACTIVE_STATUSES = {"allocating", "allocated", "ready", "releasing"}


class SessionResourceAllocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        resource_type: str,
        resource_id: str,
        provider: str | None,
        status: str = "allocated",
        metadata: dict[str, object] | None = None,
    ) -> SessionResourceAllocation:
        existing = await self.get_active_by_type(
            organization_id=organization_id,
            session_id=session_id,
            resource_type=resource_type,
            provider=provider,
        )
        if existing is not None:
            existing.resource_id = resource_id
            existing.status = status
            existing.metadata_json = metadata or existing.metadata_json or {}
            existing.updated_at = datetime.now(UTC)
            await self._session.flush()
            return existing
        row = SessionResourceAllocation(
            organization_id=organization_id,
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            provider=provider,
            status=status,
            metadata_json=metadata or {},
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_active_by_type(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        resource_type: str,
        provider: str | None = None,
    ) -> SessionResourceAllocation | None:
        statement = select(SessionResourceAllocation).where(
            SessionResourceAllocation.organization_id == organization_id,
            SessionResourceAllocation.session_id == session_id,
            SessionResourceAllocation.resource_type == resource_type,
            SessionResourceAllocation.status.in_(ACTIVE_STATUSES),
        )
        if provider is None:
            statement = statement.where(SessionResourceAllocation.provider.is_(None))
        else:
            statement = statement.where(SessionResourceAllocation.provider == provider)
        statement = statement.order_by(SessionResourceAllocation.created_at.desc()).limit(1)
        return cast(SessionResourceAllocation | None, await self._session.scalar(statement))

    async def list_active(
        self, *, organization_id: UUID, session_id: UUID
    ) -> list[SessionResourceAllocation]:
        statement = (
            select(SessionResourceAllocation)
            .where(
                SessionResourceAllocation.organization_id == organization_id,
                SessionResourceAllocation.session_id == session_id,
                SessionResourceAllocation.status.in_(ACTIVE_STATUSES),
            )
            .order_by(SessionResourceAllocation.created_at.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def list_for_session(
        self, *, organization_id: UUID, session_id: UUID
    ) -> list[SessionResourceAllocation]:
        statement = (
            select(SessionResourceAllocation)
            .where(
                SessionResourceAllocation.organization_id == organization_id,
                SessionResourceAllocation.session_id == session_id,
            )
            .order_by(SessionResourceAllocation.created_at.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def mark_status(
        self,
        row: SessionResourceAllocation,
        *,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> SessionResourceAllocation:
        row.status = status
        row.error_code = error_code
        row.error_message = error_message
        row.updated_at = datetime.now(UTC)
        if status in {"released", "release_failed"} and row.released_at is None:
            row.released_at = datetime.now(UTC)
        await self._session.flush()
        return row
