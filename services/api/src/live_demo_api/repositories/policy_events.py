"""Policy event repository placeholder.

Phase 9 policy events are persisted through audit_logs and Redis streams. This
module gives future outbox-backed policy event writes a stable import target.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PolicyEventRef:
    organization_id: UUID
    trace_id: str
    action: str
