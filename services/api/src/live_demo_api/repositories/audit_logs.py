"""Audit log repository."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        organization_id: UUID,
        actor_type: str,
        actor_id: str | None,
        action: str,
        resource_type: str | None,
        resource_id: str | None,
        metadata: dict[str, object] | None = None,
    ) -> AuditLog:
        row = AuditLog(
            organization_id=organization_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_=metadata or {},
        )
        self._session.add(row)
        await self._session.flush()
        return row
