from __future__ import annotations

import pytest

from live_demo_api.orchestration.saga import OrchestrationSaga, SagaStep, StepResult


async def test_saga_runs_steps_and_compensates_required_failure() -> None:
    events: list[str] = []

    async def ok() -> StepResult[object]:
        events.append("ok")
        return StepResult(name="ok", value=None, success=True)

    async def fail() -> StepResult[object]:
        events.append("fail")
        return StepResult(name="fail", value=None, success=False, error_code="failed")

    async def compensate(result: StepResult[object]) -> None:
        events.append(f"compensate:{result.name}")

    saga = OrchestrationSaga()

    with pytest.raises(RuntimeError):
        await saga.run(
            (
                SagaStep("ok", ok, compensate, required=True, timeout_ms=100),
                SagaStep("fail", fail, compensate, required=True, timeout_ms=100),
            )
        )

    assert events == ["ok", "fail", "compensate:ok"]


async def test_saga_continues_after_optional_failure() -> None:
    events: list[str] = []

    async def fail() -> StepResult[object]:
        events.append("optional_fail")
        return StepResult(name="optional", value=None, success=False, error_code="failed")

    async def ok() -> StepResult[object]:
        events.append("ok")
        return StepResult(name="ok", value=None, success=True)

    async def compensate(result: StepResult[object]) -> None:
        events.append(f"compensate:{result.name}")

    saga = OrchestrationSaga()

    results = await saga.run(
        (
            SagaStep("optional", fail, compensate, required=False, timeout_ms=100),
            SagaStep("ok", ok, compensate, required=True, timeout_ms=100),
        )
    )

    assert [result.success for result in results] == [False, True]
    assert events == ["optional_fail", "ok"]


@pytest.mark.parametrize("timeout_ms", [1])
async def test_saga_timeout_reports_failure(timeout_ms: int) -> None:
    async def slow() -> StepResult[object]:
        import asyncio

        await asyncio.sleep(0.1)
        return StepResult(name="slow", value=None, success=True)

    async def compensate(result: StepResult[object]) -> None:
        _ = result

    saga = OrchestrationSaga()

    with pytest.raises(TimeoutError):
        await saga.run((SagaStep("slow", slow, compensate, True, timeout_ms),))
