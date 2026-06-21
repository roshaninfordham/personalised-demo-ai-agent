"""Protected audit log query endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api import permissions
from live_demo_api.db.models import AuditLog
from live_demo_api.dependencies import get_db_session
from live_demo_api.errors import NotFoundError, ValidationAppError
from live_demo_api.rbac_dependencies import require_permission
from live_demo_api.repositories.audit_logs import AuditLogRepository
from live_demo_api.security import Principal

router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit-logs"])
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
AuditReadPrincipalDep = Annotated[Principal, Depends(require_permission(permissions.AUDIT_READ))]
AuditLimit = Annotated[int, Query(ge=1, le=100)]


@router.get("")
async def list_audit_logs(
    *,
    resource_type: str | None = None,
    resource_id: str | None = None,
    session_id: UUID | None = None,
    action: str | None = None,
    actor_id: str | None = None,
    cursor_created_at: datetime | None = None,
    cursor_audit_log_id: UUID | None = None,
    limit: AuditLimit = 25,
    db: DbSessionDep,
    principal: AuditReadPrincipalDep,
) -> dict[str, object]:
    if (cursor_created_at is None) != (cursor_audit_log_id is None):
        raise ValidationAppError(
            "Both cursor_created_at and cursor_audit_log_id are required.",
            code="invalid_audit_cursor",
        )
    rows = await AuditLogRepository(db).list_for_organization(
        organization_id=principal.organization_id,
        limit=limit,
        cursor_created_at=cursor_created_at,
        cursor_audit_log_id=cursor_audit_log_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        session_id=session_id,
        actor_id=actor_id,
    )
    return {"items": [_serialize(row) for row in rows]}


@router.get("/{audit_log_id}")
async def get_audit_log(
    *,
    audit_log_id: UUID,
    db: DbSessionDep,
    principal: AuditReadPrincipalDep,
) -> dict[str, object]:
    row = await AuditLogRepository(db).get_for_organization(
        organization_id=principal.organization_id,
        audit_log_id=audit_log_id,
    )
    if row is None:
        raise NotFoundError("Audit log not found.", code="audit_log_not_found")
    return _serialize(row)


def _serialize(row: AuditLog) -> dict[str, object]:
    return {
        "audit_log_id": str(row.audit_log_id),
        "organization_id": str(row.organization_id),
        "actor_type": row.actor_type,
        "actor_id": row.actor_id,
        "action": row.action,
        "resource_type": row.resource_type,
        "resource_id": row.resource_id,
        "session_id": str(row.session_id) if row.session_id else None,
        "risk_level": row.risk_level,
        "policy_decision": row.policy_decision,
        "reason_codes": row.reason_codes,
        "metadata": row.metadata_,
        "request_id": row.request_id,
        "trace_id": row.trace_id,
        "event_hash": row.event_hash,
        "previous_event_hash": row.previous_event_hash,
        "created_at": row.created_at.isoformat(),
    }
