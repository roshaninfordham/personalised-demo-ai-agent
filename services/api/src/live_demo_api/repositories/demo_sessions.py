"""Demo-session repository."""

from collections.abc import Sequence
from typing import cast
from uuid import UUID

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
    ) -> DemoSession:
        demo_session = DemoSession(
            organization_id=organization_id,
            product_id=product_id,
            recipe_id=recipe_id,
            status=SessionStatus.CREATED.value,
            current_phase=DemoPhase.CREATED.value,
            start_url=start_url,
            user_persona=user_persona,
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
