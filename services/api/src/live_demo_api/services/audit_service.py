"""Audit and event helper service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.db.models import Organization, User
from live_demo_api.events.event_bus import EventBus
from live_demo_api.repositories.audit_logs import AuditLogRepository
from live_demo_api.security import Principal, RequestContext
from live_demo_contracts.common import JsonValue
from live_demo_contracts.event import EventEnvelope, EventType


class AuditService:
    async def ensure_local_organization(self, db: AsyncSession, principal: Principal) -> None:
        settings = get_settings()
        if not (settings.app_env == "local" and settings.dev_allow_implicit_local_org):
            return
        if str(principal.organization_id) != settings.dev_local_organization_id:
            return
        existing = await db.scalar(
            select(Organization).where(Organization.organization_id == principal.organization_id)
        )
        if existing is None:
            db.add(
                Organization(
                    organization_id=principal.organization_id,
                    name="Local Development",
                    slug="local-development",
                    plan="local",
                )
            )
            await db.flush()
        if principal.user_id is None:
            return
        existing_user = await db.scalar(select(User).where(User.user_id == principal.user_id))
        if existing_user is None:
            db.add(
                User(
                    user_id=principal.user_id,
                    organization_id=principal.organization_id,
                    email="local@example.test",
                    display_name="Local User",
                    role=principal.role,
                )
            )
            await db.flush()

    async def audit(
        self,
        db: AsyncSession,
        *,
        principal: Principal,
        action: str,
        resource_type: str,
        resource_id: UUID | str | None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        await AuditLogRepository(db).add(
            organization_id=principal.organization_id,
            actor_type=principal.actor_type,
            actor_id=str(principal.user_id) if principal.user_id is not None else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            metadata=metadata,
        )


async def publish_event(
    event_bus: EventBus,
    *,
    organization_id: UUID,
    session_id: UUID | None,
    event_type: str,
    request_context: RequestContext,
    payload: dict[str, object],
) -> None:
    event = EventEnvelope(
        event_id=str(uuid4()),
        session_id=str(session_id) if session_id is not None else None,
        organization_id=str(organization_id),
        event_type=EventType(event_type),
        created_at=datetime.now(UTC).isoformat(),
        trace_id=request_context.trace_id or request_context.request_id,
        payload=cast(dict[str, JsonValue], payload),
    )
    await event_bus.publish(event)
