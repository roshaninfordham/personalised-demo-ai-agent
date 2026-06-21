"""Durable session resource registry."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import SessionResourceAllocation
from live_demo_api.orchestration.orchestration_types import SessionResource
from live_demo_api.repositories.session_resource_allocations import (
    SessionResourceAllocationRepository,
)
from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine


class ResourceRegistry:
    def __init__(self, db: AsyncSession, redaction: RedactionEngine | None = None) -> None:
        self._repo = SessionResourceAllocationRepository(db)
        self._redaction = redaction or RedactionEngine()

    async def register_resource(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        resource_type: str,
        resource_id: str,
        provider: str | None,
        status: str = "allocated",
        metadata: dict[str, object] | None = None,
    ) -> SessionResource:
        safe_metadata = self._redaction.redact_json(
            metadata or {}, RedactionContext.AUDIT
        ).redacted_value
        row = await self._repo.register(
            organization_id=organization_id,
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            provider=provider,
            status=status,
            metadata=safe_metadata if isinstance(safe_metadata, dict) else {},
        )
        return _to_resource(row)

    async def mark_resource_ready(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        resource_type: str,
        provider: str | None = None,
    ) -> SessionResource:
        return await self._mark(
            organization_id=organization_id,
            session_id=session_id,
            resource_type=resource_type,
            provider=provider,
            status="ready",
        )

    async def mark_resource_failed(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        resource_type: str,
        provider: str | None = None,
        error_code: str,
    ) -> SessionResource:
        return await self._mark(
            organization_id=organization_id,
            session_id=session_id,
            resource_type=resource_type,
            provider=provider,
            status="failed",
            error_code=error_code,
        )

    async def mark_resource_releasing(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        resource_type: str,
        provider: str | None = None,
    ) -> SessionResource:
        return await self._mark(
            organization_id=organization_id,
            session_id=session_id,
            resource_type=resource_type,
            provider=provider,
            status="releasing",
        )

    async def mark_resource_released(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        resource_type: str,
        provider: str | None = None,
    ) -> SessionResource:
        return await self._mark(
            organization_id=organization_id,
            session_id=session_id,
            resource_type=resource_type,
            provider=provider,
            status="released",
        )

    async def mark_resource_release_failed(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        resource_type: str,
        provider: str | None = None,
        error_code: str,
    ) -> SessionResource:
        return await self._mark(
            organization_id=organization_id,
            session_id=session_id,
            resource_type=resource_type,
            provider=provider,
            status="release_failed",
            error_code=error_code,
        )

    async def list_active_resources(
        self, *, organization_id: UUID, session_id: UUID
    ) -> tuple[SessionResource, ...]:
        rows = await self._repo.list_active(organization_id=organization_id, session_id=session_id)
        return tuple(_to_resource(row) for row in rows)

    async def list_resources(
        self, *, organization_id: UUID, session_id: UUID
    ) -> tuple[SessionResource, ...]:
        rows = await self._repo.list_for_session(
            organization_id=organization_id, session_id=session_id
        )
        return tuple(_to_resource(row) for row in rows)

    async def _mark(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        resource_type: str,
        provider: str | None,
        status: str,
        error_code: str | None = None,
    ) -> SessionResource:
        row = await self._repo.get_active_by_type(
            organization_id=organization_id,
            session_id=session_id,
            resource_type=resource_type,
            provider=provider,
        )
        if row is None:
            raise LookupError("active_resource_not_found")
        updated = await self._repo.mark_status(row, status=status, error_code=error_code)
        return _to_resource(updated)


def _to_resource(row: SessionResourceAllocation) -> SessionResource:
    return SessionResource(
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        provider=row.provider,
        status=row.status,
        metadata=row.metadata_json or {},
    )
