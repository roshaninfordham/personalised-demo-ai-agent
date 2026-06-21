"""Small saga helper for bounded resource orchestration."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StepResult[T]:
    name: str
    value: T | None
    success: bool
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class SagaStep[T]:
    name: str
    execute: Callable[[], Awaitable[StepResult[T]]]
    compensate: Callable[[StepResult[T]], Awaitable[None]]
    required: bool
    timeout_ms: int


class OrchestrationSaga:
    async def run(self, steps: tuple[SagaStep[object], ...]) -> tuple[StepResult[object], ...]:
        completed: list[StepResult[object]] = []
        try:
            for step in steps:
                result = await asyncio.wait_for(step.execute(), timeout=step.timeout_ms / 1000)
                completed.append(result)
                if step.required and not result.success:
                    raise RuntimeError(result.error_code or step.name)
        except Exception:
            for step, result in reversed(list(zip(steps, completed, strict=False))):
                if result.success:
                    await step.compensate(result)
            raise
        return tuple(completed)
