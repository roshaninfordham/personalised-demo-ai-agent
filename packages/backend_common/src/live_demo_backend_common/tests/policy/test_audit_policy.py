from __future__ import annotations

from uuid import UUID

from live_demo_backend_common.policy.audit_policy import AuditPolicy, audit_event_hash
from live_demo_backend_common.policy.policy_types import Principal


def test_audit_metadata_redacted_and_hash_deterministic() -> None:
    principal = Principal(
        organization_id=UUID("00000000-0000-0000-0000-000000000001"),
        actor_type="user",
        actor_id="00000000-0000-0000-0000-000000000002",
        role="owner",
    )
    event = AuditPolicy().build_event(
        principal=principal,
        action="browser.command.blocked",
        resource_type="browser_action",
        resource_id="act_123",
        session_id=UUID("00000000-0000-0000-0000-000000000010"),
        risk_level="blocked",
        policy_decision="blocked",
        reason_codes=("blocked_destructive_action",),
        metadata={"authorization": "Bearer abcdefghijklmnopqrstuvwxyz123456"},
        request_id="req",
        trace_id="trace",
    )
    assert event.metadata["authorization"] == "[REDACTED_SECRET]"
    assert audit_event_hash(event) == audit_event_hash(event)

