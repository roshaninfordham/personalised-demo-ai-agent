from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from live_demo_backend_common.policy.policy_types import Principal
from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine
from live_demo_policies.audit_action_catalog import AUDIT_ACTION_CATALOG


@dataclass(frozen=True, slots=True)
class AuditEvent:
    organization_id: UUID
    actor_type: str
    actor_id: str | None
    actor_role: str | None
    action: str
    resource_type: str
    resource_id: str | None
    session_id: UUID | None
    risk_level: str | None
    policy_decision: str | None
    reason_codes: tuple[str, ...]
    metadata: dict[str, Any]
    request_id: str | None
    trace_id: str
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AuditPolicy:
    def __init__(self, redaction_engine: RedactionEngine | None = None) -> None:
        self._redaction = redaction_engine or RedactionEngine()
        self.high_impact_actions = frozenset(
            cast(list[str], AUDIT_ACTION_CATALOG["high_impact_actions"])
        )

    def build_event(
        self,
        *,
        principal: Principal,
        action: str,
        resource_type: str,
        resource_id: str | None,
        session_id: UUID | None,
        risk_level: str | None,
        policy_decision: str | None,
        reason_codes: tuple[str, ...],
        metadata: dict[str, Any],
        request_id: str | None,
        trace_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditEvent:
        redacted = self._redaction.redact_json(metadata, RedactionContext.AUDIT)
        return AuditEvent(
            organization_id=principal.organization_id,
            actor_type=principal.actor_type,
            actor_id=principal.actor_id,
            actor_role=principal.role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            session_id=session_id,
            risk_level=risk_level,
            policy_decision=policy_decision,
            reason_codes=tuple(sorted(reason_codes)),
            metadata=redacted.redacted_value,
            request_id=request_id,
            trace_id=trace_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )


def audit_event_hash(event: AuditEvent, previous_event_hash: str | None = None) -> str:
    payload = asdict(event)
    payload["organization_id"] = str(event.organization_id)
    payload["session_id"] = str(event.session_id) if event.session_id else None
    payload["created_at"] = event.created_at.isoformat()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(((previous_event_hash or "") + canonical).encode()).hexdigest()
