"""Learner job envelope types."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from live_demo_learner_worker.errors import LearnerJobValidationError


class LearnerJobType(StrEnum):
    LEARN_PRODUCT_FROM_URL = "learn_product_from_url"
    SUMMARIZE_FIRST_SCREEN = "summarize_first_screen"
    EXPLORE_CANDIDATE_ACTIONS = "explore_candidate_actions"
    BUILD_DEMO_GRAPH = "build_demo_graph"
    GENERATE_DEMO_ROUTE = "generate_demo_route"
    CHUNK_PRODUCT_KNOWLEDGE = "chunk_product_knowledge"
    EMBED_KNOWLEDGE_CHUNKS = "embed_knowledge_chunks"
    REFRESH_PRODUCT_LEARNING = "refresh_product_learning"


@dataclass(frozen=True, slots=True)
class LearnerJobEnvelope:
    job_id: UUID
    organization_id: UUID
    product_id: UUID
    session_id: UUID | None
    learning_run_id: UUID
    job_type: LearnerJobType
    start_url: str
    priority: int
    attempt: int
    max_attempts: int
    created_at: datetime
    trace_id: str
    payload: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> LearnerJobEnvelope:
        try:
            return cls(
                job_id=UUID(str(data.get("job_id"))),
                organization_id=UUID(str(data.get("organization_id"))),
                product_id=UUID(str(data.get("product_id"))),
                session_id=(
                    UUID(str(data.get("session_id")))
                    if data.get("session_id") not in {None, ""}
                    else None
                ),
                learning_run_id=UUID(str(data.get("learning_run_id"))),
                job_type=LearnerJobType(str(data.get("job_type"))),
                start_url=str(data.get("start_url") or ""),
                priority=int(str(data.get("priority") or 50)),
                attempt=int(str(data.get("attempt") or 1)),
                max_attempts=int(str(data.get("max_attempts") or 3)),
                created_at=datetime.fromisoformat(str(data.get("created_at"))),
                trace_id=str(data.get("trace_id") or ""),
                payload=_payload(data.get("payload")),
            )
        except (TypeError, ValueError) as exc:
            raise LearnerJobValidationError("Invalid learner job envelope.") from exc

    @classmethod
    def create(
        cls,
        *,
        organization_id: UUID,
        product_id: UUID,
        learning_run_id: UUID,
        start_url: str,
        job_type: LearnerJobType = LearnerJobType.LEARN_PRODUCT_FROM_URL,
        session_id: UUID | None = None,
        trace_id: str = "",
        max_attempts: int = 3,
    ) -> LearnerJobEnvelope:
        return cls(
            job_id=uuid4(),
            organization_id=organization_id,
            product_id=product_id,
            session_id=session_id,
            learning_run_id=learning_run_id,
            job_type=job_type,
            start_url=start_url,
            priority=50,
            attempt=1,
            max_attempts=max_attempts,
            created_at=datetime.now(UTC),
            trace_id=trace_id,
            payload={},
        )

    def to_mapping(self) -> dict[str, str]:
        return {
            "job_id": str(self.job_id),
            "organization_id": str(self.organization_id),
            "product_id": str(self.product_id),
            "session_id": str(self.session_id) if self.session_id else "",
            "learning_run_id": str(self.learning_run_id),
            "job_type": self.job_type.value,
            "start_url": self.start_url,
            "priority": str(self.priority),
            "attempt": str(self.attempt),
            "max_attempts": str(self.max_attempts),
            "created_at": self.created_at.isoformat(),
            "trace_id": self.trace_id,
            "payload": "{}",
        }

    def next_attempt(self) -> LearnerJobEnvelope:
        return LearnerJobEnvelope(
            job_id=self.job_id,
            organization_id=self.organization_id,
            product_id=self.product_id,
            session_id=self.session_id,
            learning_run_id=self.learning_run_id,
            job_type=self.job_type,
            start_url=self.start_url,
            priority=self.priority,
            attempt=self.attempt + 1,
            max_attempts=self.max_attempts,
            created_at=self.created_at,
            trace_id=self.trace_id,
            payload=self.payload,
        )


def _payload(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}
