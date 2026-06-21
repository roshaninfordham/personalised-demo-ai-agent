from __future__ import annotations

from typing import Any


def generated_route_to_recipe_steps(route_payload: dict[str, Any]) -> list[dict[str, Any]]:
    steps = route_payload.get("steps", [])
    if not isinstance(steps, list):
        return []
    output: list[dict[str, Any]] = []
    for index, step in enumerate(steps[:50]):
        if not isinstance(step, dict):
            continue
        output.append(
            {
                "step_order": index,
                "step_key": str(step.get("step_key") or f"step_{index}"),
                "phase": str(step.get("phase") or "OVERVIEW").upper(),
                "goal": str(step.get("goal") or "Show verified product area."),
                "screen_hint": step.get("screen_hint"),
                "click_hint": step.get("recommended_action_label"),
                "talk_track": step.get("talk_track"),
                "allowed_actions": ["highlight_element", "click_element", "scroll"],
                "success_criteria": ["step shown or explained"],
                "fallback_strategy": step.get("fallback_strategy")
                or "Read the current screen and explain uncertainty.",
                "required": index == 0,
            }
        )
    return output
