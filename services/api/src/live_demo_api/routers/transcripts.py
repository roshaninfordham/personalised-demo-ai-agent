"""Transcript API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.dependencies import get_current_principal, get_db_session
from live_demo_api.security import Principal
from live_demo_api.services.transcript_service import TranscriptService
from live_demo_contracts.transcript import QuestionsResponse, TranscriptEventsResponse

router = APIRouter(prefix="/api/v1/demo-sessions/{session_id}", tags=["transcripts"])


@router.get("/transcript", response_model=TranscriptEventsResponse)
async def get_transcript(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    speaker: str | None = None,
    chunk_type: str | None = None,
    from_ms: int | None = None,
    to_ms: int | None = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> TranscriptEventsResponse:
    return await TranscriptService().list_transcript_events(
        db,
        principal,
        session_id,
        speaker=speaker,
        chunk_type=chunk_type,
        from_ms=from_ms,
        to_ms=to_ms,
        limit=limit,
        cursor=cursor,
    )


@router.get("/transcript/events", response_model=TranscriptEventsResponse)
async def get_transcript_events(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    speaker: str | None = None,
    chunk_type: str | None = None,
    from_ms: int | None = None,
    to_ms: int | None = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> TranscriptEventsResponse:
    return await get_transcript(
        session_id,
        db,
        principal,
        speaker=speaker,
        chunk_type=chunk_type,
        from_ms=from_ms,
        to_ms=to_ms,
        limit=limit,
        cursor=cursor,
    )


@router.get("/questions", response_model=QuestionsResponse)
async def get_questions(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    limit: Annotated[int | None, Query(ge=1)] = None,
) -> QuestionsResponse:
    return await TranscriptService().questions(db, principal, session_id, limit=limit)
