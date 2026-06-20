"""Transcript and browser-action read services."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.errors import NotFoundError
from live_demo_api.pagination import clamp_limit, decode_cursor, encode_cursor
from live_demo_api.repositories.actions import ActionRepository
from live_demo_api.repositories.demo_sessions import DemoSessionRepository
from live_demo_api.repositories.transcripts import TranscriptRepository
from live_demo_api.security import Principal
from live_demo_api.services.mappers import action_to_response, transcript_to_response
from live_demo_contracts.browser_action import BrowserActionsResponse
from live_demo_contracts.lead_summary import FeaturesShownResponse
from live_demo_contracts.transcript import (
    QuestionResponse,
    QuestionsResponse,
    TranscriptEventsResponse,
)


def _cursor_parts(cursor: str | None) -> tuple[datetime | None, UUID | None]:
    if cursor is None:
        return None, None
    decoded = decode_cursor(cursor, max_length=get_settings().max_cursor_length)
    if "created_at" not in decoded or "id" not in decoded:
        return None, None
    return datetime.fromisoformat(decoded["created_at"]), UUID(decoded["id"])


class TranscriptService:
    async def _ensure_session(
        self, db: AsyncSession, principal: Principal, session_id: UUID
    ) -> None:
        row = await DemoSessionRepository(db).get_session(
            organization_id=principal.organization_id,
            session_id=session_id,
        )
        if row is None:
            raise NotFoundError("Session not found.", code="session_not_found")

    async def list_transcript_events(
        self,
        db: AsyncSession,
        principal: Principal,
        session_id: UUID,
        *,
        speaker: str | None,
        chunk_type: str | None,
        from_ms: int | None,
        to_ms: int | None,
        limit: int | None,
        cursor: str | None,
    ) -> TranscriptEventsResponse:
        await self._ensure_session(db, principal, session_id)
        settings = get_settings()
        page_limit = clamp_limit(
            limit,
            default=100,
            maximum=settings.max_transcript_page_limit,
        )
        cursor_created_at, cursor_event_id = _cursor_parts(cursor)
        rows = await TranscriptRepository(db).list_events(
            organization_id=principal.organization_id,
            session_id=session_id,
            speaker=speaker,
            chunk_type=chunk_type,
            from_ms=from_ms,
            to_ms=to_ms,
            limit=page_limit + 1,
            cursor_created_at=cursor_created_at,
            cursor_event_id=cursor_event_id,
        )
        next_cursor = None
        if len(rows) > page_limit:
            last = rows[page_limit - 1]
            next_cursor = encode_cursor(
                {"created_at": last.created_at.isoformat(), "id": str(last.transcript_event_id)}
            )
            rows = rows[:page_limit]
        return TranscriptEventsResponse(
            items=[transcript_to_response(row) for row in rows],
            next_cursor=next_cursor,
        )

    async def list_browser_actions(
        self,
        db: AsyncSession,
        principal: Principal,
        session_id: UUID,
        *,
        action_type: str | None,
        policy_decision: str | None,
        success: bool | None,
        include_payload: bool,
        limit: int | None,
        cursor: str | None,
    ) -> BrowserActionsResponse:
        await self._ensure_session(db, principal, session_id)
        settings = get_settings()
        page_limit = clamp_limit(limit, default=100, maximum=settings.max_transcript_page_limit)
        cursor_created_at, cursor_action_id = _cursor_parts(cursor)
        allowed_payload = include_payload and principal.role in {"owner", "admin", "demo_builder"}
        rows = await ActionRepository(db).list_actions(
            organization_id=principal.organization_id,
            session_id=session_id,
            action_type=action_type,
            policy_decision=policy_decision,
            success=success,
            limit=page_limit + 1,
            cursor_created_at=cursor_created_at,
            cursor_action_id=cursor_action_id,
        )
        next_cursor = None
        if len(rows) > page_limit:
            last = rows[page_limit - 1]
            next_cursor = encode_cursor(
                {"created_at": last.created_at.isoformat(), "id": str(last.action_event_id)}
            )
            rows = rows[:page_limit]
        return BrowserActionsResponse(
            items=[action_to_response(row, include_payload=allowed_payload) for row in rows],
            next_cursor=next_cursor,
        )

    async def features_shown(
        self, db: AsyncSession, principal: Principal, session_id: UUID
    ) -> FeaturesShownResponse:
        await self._ensure_session(db, principal, session_id)
        return FeaturesShownResponse(
            features=[],
            source="not_available_in_phase_3",
            message="Feature tracking will be enriched by the learner in a later phase.",
        )

    async def questions(
        self,
        db: AsyncSession,
        principal: Principal,
        session_id: UUID,
        *,
        limit: int | None,
    ) -> QuestionsResponse:
        await self._ensure_session(db, principal, session_id)
        page_limit = clamp_limit(
            limit, default=100, maximum=get_settings().max_transcript_page_limit
        )
        rows = await TranscriptRepository(db).user_question_events(
            organization_id=principal.organization_id,
            session_id=session_id,
            limit=page_limit,
        )
        return QuestionsResponse(
            items=[
                QuestionResponse(
                    text=row.text,
                    source="heuristic_transcript",
                    transcript_event_id=str(row.transcript_event_id),
                    insight_id=None,
                    created_at=row.created_at.isoformat(),
                )
                for row in rows
            ],
            next_cursor=None,
        )
