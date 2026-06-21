"""Render context into stable prompt-ready dictionaries."""

import json
from dataclasses import asdict, is_dataclass
from typing import Any
from uuid import UUID

from live_demo_agent_runtime.context.context_types import RealtimeAgentContext


def _to_jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return value


def context_to_prompt_dict(context: RealtimeAgentContext) -> dict[str, Any]:
    return {
        "active_recipe_step": _to_jsonable(context.active_recipe_step),
        "current_screen": _to_jsonable(context.current_screen),
        "demo_phase": context.demo_phase,
        "persona": _to_jsonable(context.persona),
        "product_summary": _to_jsonable(context.product_summary),
        "recent_turns": _to_jsonable(context.recent_turns),
        "retrieved_knowledge": _to_jsonable(context.retrieved_knowledge),
        "safe_actions": _to_jsonable(context.safe_actions),
        "safety_rules": _to_jsonable(context.safety_rules),
        "source_map": _to_jsonable(context.source_map),
        "token_budget_report": _to_jsonable(context.token_budget_report),
        "user_utterance": context.user_utterance,
    }


def render_context_json(context: RealtimeAgentContext) -> str:
    return json.dumps(context_to_prompt_dict(context), sort_keys=True, separators=(",", ":"))
