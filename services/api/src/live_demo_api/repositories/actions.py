"""Browser/action event repository."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import ActionEvent


class ActionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_actions(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        limit: int,
        action_type: str | None = None,
        policy_decision: str | None = None,
        success: bool | None = None,
        cursor_created_at: datetime | None = None,
        cursor_action_id: UUID | None = None,
    ) -> list[ActionEvent]:
        statement = select(ActionEvent).where(
            ActionEvent.organization_id == organization_id,
            ActionEvent.session_id == session_id,
        )
        if action_type is not None:
            statement = statement.where(ActionEvent.action_type == action_type)
        if policy_decision is not None:
            statement = statement.where(ActionEvent.policy_decision == policy_decision)
        if success is not None:
            statement = statement.where(ActionEvent.success == success)
        if cursor_created_at is not None and cursor_action_id is not None:
            statement = statement.where(
                sa.or_(
                    ActionEvent.created_at > cursor_created_at,
                    sa.and_(
                        ActionEvent.created_at == cursor_created_at,
                        ActionEvent.action_event_id > cursor_action_id,
                    ),
                )
            )
        statement = statement.order_by(
            ActionEvent.created_at.asc(), ActionEvent.action_event_id.asc()
        ).limit(limit)
        return list((await self._session.scalars(statement)).all())
