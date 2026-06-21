from __future__ import annotations

from typing import Any


class RecipeStepSelector:
    def select_active_step(
        self, compiled_payload: dict[str, Any], progress: dict[str, Any]
    ) -> str | None:
        active = progress.get("active_step_key")
        if isinstance(active, str) and active:
            return active
        context = compiled_payload.get("context_payload")
        steps = context.get("steps", []) if isinstance(context, dict) else []
        if isinstance(steps, list):
            for step in steps:
                if isinstance(step, dict) and isinstance(step.get("step_key"), str):
                    return str(step["step_key"])
        return None
