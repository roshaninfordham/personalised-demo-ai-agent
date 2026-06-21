"""Append-only audit log repository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
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
        session_id: UUID | None = None,
        risk_level: str | None = None,
        policy_decision: str | None = None,
        reason_codes: Sequence[str] = (),
        request_id: str | None = None,
        trace_id: str | None = None,
        event_hash: str | None = None,
        previous_event_hash: str | None = None,
        metadata: dict[str, object] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        row = AuditLog(
            organization_id=organization_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            session_id=session_id,
            risk_level=risk_level,
            policy_decision=policy_decision,
            reason_codes=list(reason_codes),
            request_id=request_id,
            trace_id=trace_id,
            event_hash=event_hash,
            previous_event_hash=previous_event_hash,
            metadata_=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_for_organization(
        self,
        *,
        organization_id: UUID,
        audit_log_id: UUID,
    ) -> AuditLog | None:
        return cast(
            AuditLog | None,
            await self._session.scalar(
                sa.select(AuditLog).where(
                    AuditLog.organization_id == organization_id,
                    AuditLog.audit_log_id == audit_log_id,
                )
            ),
        )

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_audit_log_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        session_id: UUID | None = None,
        actor_id: str | None = None,
    ) -> list[AuditLog]:
        query = sa.select(AuditLog).where(AuditLog.organization_id == organization_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.where(AuditLog.resource_id == resource_id)
        if session_id:
            query = query.where(AuditLog.session_id == session_id)
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        if cursor_created_at and cursor_audit_log_id:
            query = query.where(
                sa.or_(
                    AuditLog.created_at < cursor_created_at,
                    sa.and_(
                        AuditLog.created_at == cursor_created_at,
                        AuditLog.audit_log_id < cursor_audit_log_id,
                    ),
                )
            )
        query = query.order_by(AuditLog.created_at.desc(), AuditLog.audit_log_id.desc()).limit(
            limit
        )
        return list((await self._session.scalars(query)).all())
