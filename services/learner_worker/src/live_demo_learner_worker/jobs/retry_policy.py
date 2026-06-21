"""Deterministic retry backoff."""

from __future__ import annotations

import hashlib
from uuid import UUID


def deterministic_jitter(job_id: UUID, attempt: int) -> float:
    digest = hashlib.sha256(f"{job_id}:{attempt}".encode()).digest()
    value = int.from_bytes(digest[:4], "big") / 2**32
    return 0.8 + 0.4 * value


def retry_delay_ms(
    *,
    job_id: UUID,
    attempt: int,
    base_delay_ms: int,
    max_delay_ms: int,
) -> int:
    delay = min(max_delay_ms, base_delay_ms * (2 ** max(0, attempt - 1)))
    rounded: int = round(delay * deterministic_jitter(job_id, attempt))
    return rounded
