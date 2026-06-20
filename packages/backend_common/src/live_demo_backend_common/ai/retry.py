from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from live_demo_backend_common.ai.errors import ProviderError


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_retries: int
    base_delay_ms: int
    max_delay_ms: int


def compute_retry_delay_ms(
    attempt_index: int,
    policy: RetryPolicy,
    *,
    rng: random.Random | None = None,
) -> int:
    random_source = rng if rng is not None else random
    upper_bound = min(policy.max_delay_ms, policy.base_delay_ms * (2**attempt_index))
    return int(random_source.uniform(0, upper_bound))


async def retry_async[T](
    operation: Callable[[], Awaitable[T]],
    policy: RetryPolicy,
) -> T:
    attempt = 0
    while True:
        try:
            return await operation()
        except ProviderError as exc:
            if not exc.retryable or attempt >= policy.max_retries:
                raise
            delay_ms = compute_retry_delay_ms(attempt, policy)
            await asyncio.sleep(delay_ms / 1000)
            attempt += 1
