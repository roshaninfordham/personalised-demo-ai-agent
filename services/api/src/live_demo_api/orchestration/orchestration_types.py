"""Typed request/result objects for session orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

RuntimeState = Literal[
    "created",
    "prewarming",
    "ready",
    "degraded_ready",
    "waiting_for_user",
    "live",
    "live_degraded",
    "recovery",
    "ending",
    "finalizing",
    "completed",
    "completed_with_warnings",
    "failed",
]

ResourceType = Literal[
    "browser_session",
    "voice_session",
    "transport_session",
    "learner_run",
    "compiled_recipe",
    "redis_live_state",
    "object_artifact",
]

ResourceStatus = Literal[
    "allocating",
    "allocated",
    "ready",
    "failed",
    "releasing",
    "released",
    "release_failed",
]


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class ReadinessState:
    score: float
    browser_session_ready: bool = False
    url_loaded: bool = False
    first_screen_read: bool = False
    safe_action_count: int = 0
    voice_session_ready: bool = False
    join_config_ready: bool = False
    recipe_compiled: bool = False
    learner_enqueued: bool = False
    provider_warmed_count: int = 0
    provider_required_count: int = 3
    degraded_reasons: tuple[str, ...] = ()

    @property
    def safe_actions_available(self) -> float:
        return min(1.0, self.safe_action_count / 3)

    @property
    def providers_warmed(self) -> float:
        if self.provider_required_count <= 0:
            return 1.0
        return min(1.0, self.provider_warmed_count / self.provider_required_count)


@dataclass(frozen=True, slots=True)
class SessionResource:
    resource_type: str
    resource_id: str
    provider: str | None
    status: str
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RecoveryState:
    session_id: UUID
    active: bool
    reason_code: str
    attempt_count: int
    max_attempts: int
    started_at: datetime
    last_attempt_at: datetime | None = None
    last_action: str | None = None
    resolved: bool = False


@dataclass(frozen=True, slots=True)
class PrewarmSessionRequest:
    organization_id: UUID
    session_id: UUID
    trace_id: str
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class PrewarmSessionResult:
    session_id: UUID
    status: str
    runtime_state: RuntimeState
    readiness: ReadinessState
    resources: tuple[SessionResource, ...]
    join_config: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class StartLiveSessionRequest:
    organization_id: UUID
    session_id: UUID
    trace_id: str
    idempotency_key: str | None = None
    transport_connected: bool = False


@dataclass(frozen=True, slots=True)
class LiveSessionStartResult:
    session_id: UUID
    status: str
    runtime_state: RuntimeState
    join_config: dict[str, object]
    greeting_dispatched: bool


@dataclass(frozen=True, slots=True)
class RecoverSessionRequest:
    organization_id: UUID
    session_id: UUID
    reason_code: str
    trace_id: str


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    session_id: UUID
    recovered: bool
    decision: str
    attempt_count: int
    reason_code: str
    safe_message: str


@dataclass(frozen=True, slots=True)
class ShutdownSessionRequest:
    organization_id: UUID
    session_id: UUID
    reason: str | None
    trace_id: str
    idempotency_key: str | None = None
    force: bool = False


@dataclass(frozen=True, slots=True)
class ShutdownSessionResult:
    session_id: UUID
    status: str
    completed_with_warnings: bool
    resources_released: tuple[str, ...]
    summary_status: str
    warnings: tuple[str, ...]
