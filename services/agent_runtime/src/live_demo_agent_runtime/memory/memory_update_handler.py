"""Validate, dedupe, persist, and event memory updates."""

from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.memory.lead_insight_repository import LeadInsightRepository
from live_demo_agent_runtime.memory.memory_deduper import (
    MemoryDeduper,
    memory_content_hash,
    merge_memory_update,
)
from live_demo_agent_runtime.memory.memory_scoring import score_memory_importance
from live_demo_agent_runtime.memory.memory_types import (
    MEMORY_TYPES,
    MemoryHandleResult,
    MemoryUpdate,
    StoredMemory,
)

SECRET_MARKERS = (
    "api_key",
    "password",
    "secret",
    "token",
    "private_key",
    "client_secret",
    "refresh_token",
    "access_token",
    "credit card",
    "ssn",
)


class MemoryUpdateHandler:
    def __init__(
        self,
        *,
        settings: AgentRuntimeSettings,
        repository: LeadInsightRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._event_publisher = event_publisher
        self._deduper = MemoryDeduper(
            similarity_threshold=settings.memory_update_dedupe_similarity_threshold,
            max_candidates=settings.memory_dedupe_max_candidates,
        )

    async def handle_updates(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        updates: Iterable[MemoryUpdate],
        trace_id: str,
    ) -> MemoryHandleResult:
        if not self._settings.memory_updates_enabled:
            return MemoryHandleResult(accepted=(), rejected=("memory_disabled",), merged=())
        existing = await self._repository.list_for_session(
            organization_id=organization_id,
            demo_session_id=demo_session_id,
        )
        accepted: list[StoredMemory] = []
        merged: list[StoredMemory] = []
        rejected: list[str] = []
        for update in tuple(updates)[: self._settings.memory_update_max_per_turn]:
            normalized = self._normalize_update(update)
            rejection = self._rejection_reason(normalized)
            if rejection is not None:
                rejected.append(rejection)
                if rejection == "secret_like":
                    await self._publish_rejected_secret(
                        organization_id=organization_id,
                        demo_session_id=demo_session_id,
                        trace_id=trace_id,
                    )
                continue
            duplicate = self._deduper.find_duplicate(normalized, existing)
            if duplicate is not None:
                merged_update = merge_memory_update(duplicate, normalized)
                stored = StoredMemory(
                    memory_id=duplicate.memory_id,
                    organization_id=organization_id,
                    demo_session_id=demo_session_id,
                    update=merged_update,
                    content_hash=duplicate.content_hash,
                    created_at=duplicate.created_at,
                    updated_at=datetime.now(UTC),
                )
                await self._repository.upsert_memory(stored)
                merged.append(stored)
                continue
            stored = StoredMemory(
                memory_id=str(uuid4()),
                organization_id=organization_id,
                demo_session_id=demo_session_id,
                update=normalized,
                content_hash=memory_content_hash(normalized.type, normalized.content),
            )
            await self._repository.upsert_memory(stored)
            accepted.append(stored)
            existing = (*existing, stored)
        for stored in (*accepted, *merged):
            await self._publish_memory_updated(stored, trace_id=trace_id)
        return MemoryHandleResult(
            accepted=tuple(accepted),
            rejected=tuple(rejected),
            merged=tuple(merged),
        )

    def _normalize_update(self, update: MemoryUpdate) -> MemoryUpdate:
        importance = update.importance
        if importance <= 0:
            importance = score_memory_importance(update)
        return MemoryUpdate(
            type=update.type,
            content=" ".join(update.content.split()),
            confidence=round(max(0.0, min(1.0, update.confidence)), 4),
            importance=round(max(0.0, min(1.0, importance)), 4),
            evidence_transcript_event_ids=update.evidence_transcript_event_ids[:10],
            evidence_screen_ids=update.evidence_screen_ids[:10],
            evidence_action_ids=update.evidence_action_ids[:10],
        )

    def _rejection_reason(self, update: MemoryUpdate) -> str | None:
        if update.type not in MEMORY_TYPES:
            return "invalid_type"
        if not update.has_evidence():
            return "missing_evidence"
        if update.confidence < self._settings.memory_update_min_confidence:
            return "low_confidence"
        if update.importance < self._settings.memory_update_min_importance:
            return "low_importance"
        if _contains_secret_like(update.content):
            return "secret_like"
        return None

    async def _publish_memory_updated(self, stored: StoredMemory, *, trace_id: str) -> None:
        await self._event_publisher.publish(
            organization_id=stored.organization_id,
            demo_session_id=stored.demo_session_id,
            event_type="memory.updated",
            trace_id=trace_id,
            payload={
                "memory_id": stored.memory_id,
                "type": stored.update.type,
                "confidence": stored.update.confidence,
                "importance": stored.update.importance,
            },
        )

    async def _publish_rejected_secret(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        trace_id: str,
    ) -> None:
        await self._event_publisher.publish(
            organization_id=organization_id,
            demo_session_id=demo_session_id,
            event_type="memory.rejected_secret_like",
            trace_id=trace_id,
            payload={"reason": "secret_like"},
        )


def _contains_secret_like(value: str) -> bool:
    normalized = value.lower()
    return any(marker in normalized for marker in SECRET_MARKERS)
