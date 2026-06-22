"""CRM export persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import CrmExport
from live_demo_api.post_demo.crm.crm_types import CrmExportResult


class CrmExportRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert_result(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        lead_summary_id: UUID,
        provider: str,
        payload: dict[str, Any],
        result: CrmExportResult,
        dry_run: bool,
        idempotency_key: str,
    ) -> CrmExport:
        now = datetime.now(UTC)
        statement = (
            insert(CrmExport)
            .values(
                organization_id=organization_id,
                session_id=session_id,
                lead_summary_id=lead_summary_id,
                provider=provider,
                adapter_version="v1",
                payload=payload,
                redacted_payload=result.redacted_payload,
                status=result.status,
                dry_run=dry_run,
                external_object_ids=result.external_object_ids,
                idempotency_key=idempotency_key,
                error_code=result.error_code,
                error_message=result.error_message,
                sent_at=now if result.status == "sent" else None,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=[
                    CrmExport.organization_id,
                    CrmExport.provider,
                    CrmExport.idempotency_key,
                ],
                index_where=text("idempotency_key <> ''"),
                set_={
                    "status": result.status,
                    "redacted_payload": result.redacted_payload,
                    "external_object_ids": result.external_object_ids,
                    "error_code": result.error_code,
                    "error_message": result.error_message,
                    "updated_at": now,
                },
            )
            .returning(CrmExport)
        )
        return (await self._db.scalars(statement)).one()

    async def list_for_session(
        self, *, organization_id: UUID, session_id: UUID, limit: int = 100
    ) -> list[CrmExport]:
        statement = (
            select(CrmExport)
            .where(
                CrmExport.organization_id == organization_id,
                CrmExport.session_id == session_id,
            )
            .order_by(CrmExport.created_at.desc(), CrmExport.crm_export_id.desc())
            .limit(limit)
        )
        return list((await self._db.scalars(statement)).all())

    async def get_for_session(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        crm_export_id: UUID,
    ) -> CrmExport | None:
        statement = select(CrmExport).where(
            CrmExport.organization_id == organization_id,
            CrmExport.session_id == session_id,
            CrmExport.crm_export_id == crm_export_id,
        )
        return cast(CrmExport | None, await self._db.scalar(statement))
