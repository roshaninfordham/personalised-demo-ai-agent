from __future__ import annotations

from pathlib import Path
from typing import ClassVar
from uuid import UUID

import pytest

from live_demo_api.security import Principal, RequestContext
from live_demo_api.services import audit_service as audit_module
from live_demo_api.services.audit_service import AuditService

ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
USER_ID = UUID("00000000-0000-0000-0000-000000000002")
SESSION_ID = UUID("00000000-0000-0000-0000-000000000010")


class FakeAuditLogRepository:
    rows: ClassVar[list[dict[str, object]]] = []

    def __init__(self, session: object) -> None:
        self._session = session

    async def add(self, **kwargs: object) -> object:
        self.rows.append(kwargs)
        return kwargs


@pytest.mark.asyncio
async def test_audit_service_redacts_metadata_and_writes_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeAuditLogRepository.rows = []
    monkeypatch.setattr(audit_module, "AuditLogRepository", FakeAuditLogRepository)
    principal = Principal(
        organization_id=ORG_ID,
        user_id=USER_ID,
        role="owner",
        actor_type="user",
    )
    await AuditService().record_event(
        object(),  # type: ignore[arg-type]
        principal=principal,
        action="browser.command.blocked",
        resource_type="browser_action",
        resource_id="act_123",
        session_id=SESSION_ID,
        risk_level="blocked",
        policy_decision="blocked",
        reason_codes=("blocked_destructive_action",),
        metadata={"api_key": "secret-value", "safe": "visible"},
        request_context=RequestContext(request_id="req", trace_id="trace"),
    )
    assert len(FakeAuditLogRepository.rows) == 1
    row = FakeAuditLogRepository.rows[0]
    assert row["event_hash"]
    assert row["reason_codes"] == ("blocked_destructive_action",)
    assert row["metadata"] == {"api_key": "[REDACTED_SECRET]", "safe": "visible"}


def test_audit_migration_enforces_append_only() -> None:
    migration = Path("services/api/alembic/versions/0003_phase_9_policy_audit.py").read_text()
    assert "prevent_audit_log_modification" in migration
    assert "trg_prevent_audit_log_update" in migration
    assert "trg_prevent_audit_log_delete" in migration
