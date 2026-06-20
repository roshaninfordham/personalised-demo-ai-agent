from __future__ import annotations

import random

import pytest

from live_demo_backend_common.ai.errors import ProviderUnavailableError
from live_demo_backend_common.ai.retry import RetryPolicy, compute_retry_delay_ms, retry_async


def test_retry_delay_can_be_seeded() -> None:
    rng = random.Random(1)  # noqa: S311 - deterministic retry jitter test only.
    assert compute_retry_delay_ms(0, RetryPolicy(2, 100, 1000), rng=rng) == 13


@pytest.mark.asyncio
async def test_retry_only_retryable_errors() -> None:
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ProviderUnavailableError(
                provider_name="p",
                model_name="m",
                operation="op",
                retryable=True,
                status_code=503,
                safe_message="retry",
            )
        return "ok"

    result = await retry_async(
        operation,
        RetryPolicy(max_retries=1, base_delay_ms=0, max_delay_ms=0),
    )
    assert result == "ok"
    assert attempts == 2
