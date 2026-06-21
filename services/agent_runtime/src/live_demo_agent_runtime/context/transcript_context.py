"""Transcript context helpers."""

from live_demo_agent_runtime.context.context_types import RecentTurnContext


def recent_turn_window(
    turns: list[RecentTurnContext],
    *,
    max_turns: int,
) -> tuple[RecentTurnContext, ...]:
    return tuple(turns[-max_turns:])
