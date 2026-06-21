from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

PolicyDecisionValue = Literal["allowed", "blocked", "confirmation_required", "not_applicable"]
RiskLevel = Literal["low", "medium", "high", "blocked", "unknown"]


@dataclass(frozen=True, slots=True)
class PolicyActor:
    actor_type: Literal["user", "agent", "system", "service"]
    actor_id: str | None
    role: str


@dataclass(frozen=True, slots=True)
class PolicyResource:
    resource_type: str
    resource_id: str | None


@dataclass(frozen=True, slots=True)
class MatchedPolicyRule:
    rule_id: str
    category: str
    phrase: str | None = None


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    decision_id: UUID
    decision: PolicyDecisionValue
    risk_level: RiskLevel
    risk_score: float
    requires_confirmation: bool
    reason_codes: tuple[str, ...]
    matched_rules: tuple[MatchedPolicyRule, ...]
    actor: PolicyActor
    resource: PolicyResource
    organization_id: UUID
    session_id: UUID | None
    trace_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def make(
        cls,
        *,
        decision: PolicyDecisionValue,
        risk_level: RiskLevel,
        risk_score: float,
        requires_confirmation: bool,
        reason_codes: list[str],
        matched_rules: list[MatchedPolicyRule],
        actor: PolicyActor,
        resource: PolicyResource,
        organization_id: UUID,
        session_id: UUID | None,
        trace_id: str,
    ) -> PolicyDecision:
        return cls(
            decision_id=uuid4(),
            decision=decision,
            risk_level=risk_level,
            risk_score=max(0.0, min(1.0, risk_score)),
            requires_confirmation=requires_confirmation,
            reason_codes=tuple(dict.fromkeys(reason_codes)),
            matched_rules=tuple(matched_rules),
            actor=actor,
            resource=resource,
            organization_id=organization_id,
            session_id=session_id,
            trace_id=trace_id,
        )


@dataclass(frozen=True, slots=True)
class ConfirmationContext:
    confirmed: bool
    confirmation_token: str | None = None
    confirmed_by_actor_id: str | None = None
    confirmed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Principal:
    organization_id: UUID
    actor_type: Literal["user", "agent", "system", "service"]
    actor_id: str | None
    role: Literal["owner", "admin", "demo_builder", "viewer", "agent_runtime"]
    session_id: UUID | None = None
    scopes: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class RedactionFinding:
    finding_type: str
    redaction_mode: str
    path: str | None = None
    start: int | None = None
    end: int | None = None
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class RedactionResult:
    redacted_value: Any
    applied: bool
    findings: tuple[RedactionFinding, ...]
    original_hash: str | None
