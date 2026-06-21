"""Bounded task concurrency helper."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class BoundedTaskRunner:
    def __init__(self, limit: int) -> None:
        self._semaphore = asyncio.Semaphore(limit)

    async def run(self, factory: Callable[[], Awaitable[T]]) -> T:
        async with self._semaphore:
            return await factory()
