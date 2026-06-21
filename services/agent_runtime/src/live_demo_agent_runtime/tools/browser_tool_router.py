"""Deterministic safe-action router for browser tools."""

import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from live_demo_agent_runtime.tools import tool_errors
from live_demo_agent_runtime.tools.browser_tool_client import BrowserToolClient
from live_demo_agent_runtime.tools.browser_tool_results import ToolRouteRequest, ToolRouteResult


class InMemoryToolIdempotencyStore:
    def __init__(self) -> None:
        self._keys: dict[tuple[UUID, UUID, str], UUID] = {}

    def set_once(self, demo_session_id: UUID, turn_id: UUID, action_id: str) -> bool:
        key = (demo_session_id, turn_id, action_id)
        if key in self._keys:
            return False
        self._keys[key] = uuid4()
        return True


class BrowserToolRouter:
    def __init__(
        self,
        *,
        browser_client: BrowserToolClient,
        idempotency_store: InMemoryToolIdempotencyStore | None = None,
    ) -> None:
        self._browser_client = browser_client
        self._idempotency_store = idempotency_store or InMemoryToolIdempotencyStore()

    async def route(self, request: ToolRouteRequest) -> ToolRouteResult:
        started = time.perf_counter_ns()
        decision_action = request.agent_decision.browser_action
        if decision_action is None:
            return _result(
                started,
                executed=False,
                error_code=tool_errors.NO_ACTION,
                policy_decision="no_action",
            )
        actions = {action.action_id: action for action in request.current_context.safe_actions}
        safe_action = actions.get(decision_action.action_id)
        if safe_action is None:
            return _result(
                started,
                decision_action.action_id,
                decision_action.tool_name,
                tool_errors.INVALID_ACTION_ID,
            )
        mismatch = not _tool_matches(decision_action.tool_name, safe_action.action_type)
        if mismatch:
            return _result(
                started,
                decision_action.action_id,
                decision_action.tool_name,
                tool_errors.TOOL_MISMATCH,
            )
        if safe_action.expires_at is not None and safe_action.expires_at < datetime.now(UTC):
            return _result(
                started,
                decision_action.action_id,
                decision_action.tool_name,
                tool_errors.ACTION_EXPIRED,
            )
        if safe_action.risk_level == "blocked":
            return _result(
                started,
                decision_action.action_id,
                decision_action.tool_name,
                tool_errors.RISK_BLOCKED,
            )
        if safe_action.risk_level == "high":
            return _result(
                started,
                decision_action.action_id,
                decision_action.tool_name,
                tool_errors.CONFIRMATION_REQUIRED,
                risk_level=safe_action.risk_level,
            )
        if not self._idempotency_store.set_once(
            request.demo_session_id,
            request.active_turn_id,
            decision_action.action_id,
        ):
            return _result(
                started,
                decision_action.action_id,
                decision_action.tool_name,
                tool_errors.DUPLICATE_ACTION_IGNORED,
                executed=False,
                risk_level=safe_action.risk_level,
            )
        browser_result = await self._browser_client.execute_action(
            organization_id=request.organization_id,
            demo_session_id=request.demo_session_id,
            action_id=decision_action.action_id,
            tool_name=decision_action.tool_name,
            arguments=decision_action.arguments,
            trace_id=request.trace_id,
        )
        success = browser_result.get("success") is True
        return ToolRouteResult(
            executed=True,
            tool_name=decision_action.tool_name,
            action_id=decision_action.action_id,
            success=success,
            policy_decision="allowed",
            risk_level=safe_action.risk_level,
            browser_action_result=browser_result,
            error_code=None if success else tool_errors.BROWSER_ACTION_FAILED,
            error_message=None if success else "Browser action failed.",
            latency_ms=_elapsed_ms(started),
        )


def _tool_matches(tool_name: str, action_type: str) -> bool:
    return tool_name == action_type or (
        tool_name == "type_demo_text" and action_type == "type_into_element"
    )


def _result(
    started_ns: int,
    action_id: str | None = None,
    tool_name: str | None = None,
    error_code: str | None = None,
    *,
    executed: bool = False,
    policy_decision: str | None = None,
    risk_level: str | None = None,
) -> ToolRouteResult:
    return ToolRouteResult(
        executed=executed,
        tool_name=tool_name,
        action_id=action_id,
        success=False if error_code and error_code != tool_errors.NO_ACTION else None,
        policy_decision=policy_decision or error_code,
        risk_level=risk_level,
        browser_action_result=None,
        error_code=error_code,
        error_message=error_code,
        latency_ms=_elapsed_ms(started_ns),
    )


def _elapsed_ms(started_ns: int) -> int:
    return int((time.perf_counter_ns() - started_ns) / 1_000_000)
