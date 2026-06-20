"""Demo-session repository."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import DemoSession
from live_demo_api.db.types import DemoPhase, SessionStatus


class DemoSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        start_url: str,
        recipe_id: UUID | None = None,
        user_persona: str | None = None,
        user_company: str | None = None,
        user_display_name: str | None = None,
        user_email: str | None = None,
    ) -> DemoSession:
        demo_session = DemoSession(
            organization_id=organization_id,
            product_id=product_id,
            recipe_id=recipe_id,
            status=SessionStatus.CREATED.value,
            current_phase=DemoPhase.CREATED.value,
            start_url=start_url,
            user_persona=user_persona,
            user_company=user_company,
            user_display_name=user_display_name,
            user_email=user_email,
        )
        self._session.add(demo_session)
        await self._session.flush()
        return demo_session

    async def get_session(self, *, organization_id: UUID, session_id: UUID) -> DemoSession | None:
        statement = select(DemoSession).where(
            DemoSession.organization_id == organization_id,
            DemoSession.session_id == session_id,
            DemoSession.deleted_at.is_(None),
        )
        return cast(DemoSession | None, await self._session.scalar(statement))

    async def list_sessions(
        self,
        *,
        organization_id: UUID,
        limit: int,
        product_id: UUID | None = None,
        status: SessionStatus | None = None,
        cursor_created_at: datetime | None = None,
        cursor_session_id: UUID | None = None,
    ) -> list[DemoSession]:
        statement = select(DemoSession).where(
            DemoSession.organization_id == organization_id,
            DemoSession.deleted_at.is_(None),
        )
        if product_id is not None:
            statement = statement.where(DemoSession.product_id == product_id)
        if status is not None:
            statement = statement.where(DemoSession.status == status.value)
        if cursor_created_at is not None and cursor_session_id is not None:
            statement = statement.where(
                sa.or_(
                    DemoSession.created_at < cursor_created_at,
                    sa.and_(
                        DemoSession.created_at == cursor_created_at,
                        DemoSession.session_id < cursor_session_id,
                    ),
                )
            )
        statement = statement.order_by(
            DemoSession.created_at.desc(), DemoSession.session_id.desc()
        ).limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def set_status(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        status: SessionStatus,
        current_phase: DemoPhase,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
    ) -> DemoSession | None:
        row = await self.get_session(organization_id=organization_id, session_id=session_id)
        if row is None:
            return None
        row.status = status.value
        row.current_phase = current_phase.value
        if started_at is not None and row.started_at is None:
            row.started_at = started_at
        if ended_at is not None and row.ended_at is None:
            row.ended_at = ended_at
        await self._session.flush()
        return row

    async def list_active_sessions(
        self,
        *,
        organization_id: UUID,
        statuses: Sequence[SessionStatus],
        limit: int = 50,
    ) -> list[DemoSession]:
        statement = (
            select(DemoSession)
            .where(
                DemoSession.organization_id == organization_id,
                DemoSession.status.in_([status.value for status in statuses]),
                DemoSession.deleted_at.is_(None),
            )
            .order_by(DemoSession.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())


def utc_now() -> datetime:
    return datetime.now(UTC)
