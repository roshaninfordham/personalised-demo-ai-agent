"""Audit and event helper service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.db.models import Organization, User
from live_demo_api.events.event_bus import EventBus
from live_demo_api.repositories.audit_logs import AuditLogRepository
from live_demo_api.security import Principal, RequestContext
from live_demo_backend_common.policy.audit_policy import AuditPolicy, audit_event_hash
from live_demo_backend_common.policy.policy_types import Principal as PolicyPrincipal
from live_demo_contracts.common import JsonValue
from live_demo_contracts.event import EventEnvelope, EventType

ActorType = Literal["user", "agent", "system", "service"]
PolicyRole = Literal["owner", "admin", "demo_builder", "viewer", "agent_runtime"]


def to_policy_principal(principal: Principal, *, session_id: UUID | None = None) -> PolicyPrincipal:
    role = (
        principal.role
        if principal.role in {"owner", "admin", "demo_builder", "viewer", "agent_runtime"}
        else "viewer"
    )
    return PolicyPrincipal(
        organization_id=principal.organization_id,
        actor_type=cast(ActorType, principal.actor_type),
        actor_id=str(principal.user_id) if principal.user_id is not None else None,
        role=cast(PolicyRole, role),
        session_id=session_id,
    )


class AuditService:
    def __init__(self, audit_policy: AuditPolicy | None = None) -> None:
        self._policy = audit_policy or AuditPolicy()

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

    async def record_event(
        self,
        db: AsyncSession,
        *,
        principal: Principal,
        action: str,
        resource_type: str,
        resource_id: UUID | str | None,
        session_id: UUID | None = None,
        risk_level: str | None = None,
        policy_decision: str | None = None,
        reason_codes: tuple[str, ...] = (),
        metadata: dict[str, object] | None = None,
        request_context: RequestContext | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        event = self._policy.build_event(
            principal=to_policy_principal(principal, session_id=session_id),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            session_id=session_id,
            risk_level=risk_level,
            policy_decision=policy_decision,
            reason_codes=reason_codes,
            metadata=metadata or {},
            request_id=request_context.request_id if request_context else None,
            trace_id=(
                request_context.trace_id
                if request_context and request_context.trace_id
                else request_context.request_id
                if request_context
                else ""
            ),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await AuditLogRepository(db).add(
            organization_id=event.organization_id,
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            session_id=event.session_id,
            risk_level=event.risk_level,
            policy_decision=event.policy_decision,
            reason_codes=event.reason_codes,
            request_id=event.request_id,
            trace_id=event.trace_id,
            event_hash=audit_event_hash(event),
            previous_event_hash=None,
            metadata=cast(dict[str, object], event.metadata),
            ip_address=event.ip_address,
            user_agent=event.user_agent,
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
