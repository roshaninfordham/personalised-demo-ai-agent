from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine
from live_demo_backend_common.recipes.recipe_defaults import DEFAULT_NEVER_CLICK
from live_demo_backend_common.recipes.recipe_normalizer import slug_key
from live_demo_backend_common.recipes.recipe_types import DemoRecipe, RecipeEngineLimits
from live_demo_backend_common.recipes.recipe_validator import RecipeValidator

PERSONAS = (
    "founder",
    "operator",
    "sales",
    "marketing",
    "analytics",
    "engineering",
    "product",
    "executive",
)


@dataclass(frozen=True, slots=True)
class RecipeGenerationInput:
    organization_id: str
    product_id: str
    product_name: str | None
    product_url: str
    text_guidance: str
    target_persona: str | None = None
    product_summary: str | None = None
    available_screen_summaries: tuple[dict[str, Any], ...] = ()
    available_safe_actions: tuple[dict[str, Any], ...] = ()
    default_never_click: tuple[str, ...] = DEFAULT_NEVER_CLICK
    trace_id: str = ""


@dataclass(frozen=True, slots=True)
class GuidanceExtraction:
    show_items: tuple[str, ...]
    avoid_items: tuple[str, ...]
    persona: str | None
    ordered_flow: tuple[str, ...]
    redacted_guidance: str
    redaction_applied: bool


class DeterministicGuidanceExtractor:
    def __init__(self, redaction_engine: RedactionEngine | None = None) -> None:
        self._redaction = redaction_engine or RedactionEngine()

    def extract(self, text_guidance: str, target_persona: str | None = None) -> GuidanceExtraction:
        redacted = self._redaction.redact_text(text_guidance, RedactionContext.PROMPT)
        text = str(redacted.redacted_value)
        lowered = text.lower()
        show_items = _extract_after_keywords(text, ("show", "demo", "walk through", "highlight"))
        avoid_items = _extract_after_keywords(text, ("avoid", "don't click", "never click", "skip"))
        persona = target_persona or next((item for item in PERSONAS if item in lowered), None)
        ordered_flow = _ordered_flow(text)
        return GuidanceExtraction(
            show_items=tuple(show_items),
            avoid_items=tuple(avoid_items),
            persona=persona,
            ordered_flow=tuple(ordered_flow),
            redacted_guidance=text,
            redaction_applied=redacted.applied,
        )


class TextGuidanceRecipeGenerator:
    def __init__(
        self,
        *,
        validator: RecipeValidator | None = None,
        extractor: DeterministicGuidanceExtractor | None = None,
        limits: RecipeEngineLimits | None = None,
    ) -> None:
        self._limits = limits or RecipeEngineLimits()
        self._validator = validator
        self._extractor = extractor or DeterministicGuidanceExtractor()

    def generate_fallback(self, request: RecipeGenerationInput) -> dict[str, Any]:
        extraction = self._extractor.extract(request.text_guidance, request.target_persona)
        flow = list(extraction.ordered_flow or extraction.show_items)
        never_click = list(dict.fromkeys([*DEFAULT_NEVER_CLICK, *extraction.avoid_items]))
        steps = [
            {
                "step_order": 0,
                "step_key": "overview",
                "phase": "OVERVIEW",
                "goal": "Show what is visible on the first screen.",
                "screen_hint": "dashboard, overview, home, landing page",
                "click_hint": None,
                "talk_track": "Start with what can be verified on screen.",
                "allowed_actions": ["read_current_screen", "highlight_element", "scroll"],
                "success_criteria": ["current screen summarized"],
                "fallback_strategy": "Read the current screen and explain uncertainty.",
                "required": True,
                "confidence": 0.72,
                "source_references": ["guidance"],
            }
        ]
        core_goal = (
            f"Show {flow[1] if len(flow) > 1 else flow[0]}"
            if flow
            else "Show the safest visible primary workflow if available."
        )
        steps.append(
            {
                "step_order": 1,
                "step_key": slug_key(core_goal, "core_workflow"),
                "phase": "CORE_WORKFLOW",
                "goal": core_goal,
                "screen_hint": "main dashboard or primary navigation",
                "click_hint": ", ".join(flow)
                if flow
                else "Add, Create, Reports, Analytics, Metrics, Dashboard",
                "talk_track": "Show the most relevant safe visible action.",
                "allowed_actions": ["highlight_element", "click_element", "scroll"],
                "success_criteria": ["safe action executed or explained"],
                "fallback_strategy": (
                    "If no safe workflow is visible, ask what the user wants to inspect."
                ),
                "required": False,
                "confidence": 0.62,
                "source_references": ["guidance"],
            }
        )
        steps.append(
            {
                "step_order": 2,
                "step_key": "recap",
                "phase": "SUMMARY",
                "goal": "Recap only verified product areas shown.",
                "screen_hint": None,
                "click_hint": None,
                "talk_track": "Summarize verified screens and user interests.",
                "allowed_actions": [],
                "success_criteria": ["recap delivered"],
                "fallback_strategy": "Explain what was verified and what remains unknown.",
                "required": True,
                "confidence": 0.70,
                "source_references": ["guidance"],
            }
        )
        recipe = {
            "recipe_name": f"{request.product_name or 'Generated Product'} Demo",
            "target_persona": extraction.persona,
            "demo_goal": "Give a grounded overview of the product and show safe visible workflows.",
            "global_talk_track": request.product_summary,
            "never_click": never_click,
            "allowed_domains": [],
            "steps": steps[: self._limits.max_steps],
            "status": "draft",
        }
        validator = self._validator or RecipeValidator(product_url=request.product_url)
        validation = validator.validate(recipe)
        if validation.valid and validation.normalized_recipe is not None:
            return _recipe_to_dict(validation.normalized_recipe)
        return recipe


def _extract_after_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    results: list[str] = []
    for keyword in keywords:
        pattern = re.compile(rf"\b{re.escape(keyword)}\b([^.;\n]+)", re.IGNORECASE)
        for match in pattern.finditer(text):
            for item in re.split(r",|\bthen\b|\bnext\b|\band\b", match.group(1)):
                clean = item.strip(" :.-")
                if clean and len(clean) <= 80:
                    results.append(clean)
    return list(dict.fromkeys(results))[:10]


def _ordered_flow(text: str) -> list[str]:
    flow: list[str] = []
    for marker in ("first", "then", "next", "finally"):
        match = re.search(rf"\b{marker}\b([^.;\n]+)", text, flags=re.IGNORECASE)
        if match:
            flow.append(match.group(1).strip(" :.-"))
    return [item for item in flow if item][:10]


def _recipe_to_dict(recipe: DemoRecipe) -> dict[str, Any]:
    return {
        "recipe_name": recipe.recipe_name,
        "target_persona": recipe.target_persona,
        "demo_goal": recipe.demo_goal,
        "global_talk_track": recipe.global_talk_track,
        "never_click": list(recipe.never_click),
        "allowed_domains": list(recipe.allowed_domains),
        "allowed_form_fields": [
            {
                "field_label_pattern": item.field_label_pattern,
                "field_type": item.field_type,
                "max_chars": item.max_chars,
            }
            for item in recipe.allowed_form_fields
        ],
        "confirmation_required_actions": [
            {
                "action_type": item.action_type,
                "label_pattern": item.label_pattern,
                "reason": item.reason,
            }
            for item in recipe.confirmation_required_actions
        ],
        "steps": [
            {
                "step_order": step.step_order,
                "step_key": step.step_key,
                "phase": step.phase,
                "goal": step.goal,
                "screen_hint": step.screen_hint,
                "click_hint": step.click_hint,
                "talk_track": step.talk_track,
                "allowed_actions": list(step.allowed_actions),
                "success_criteria": list(step.success_criteria),
                "fallback_strategy": step.fallback_strategy,
                "max_attempts": step.max_attempts,
                "required": step.required,
                "confidence": step.confidence,
                "source_references": list(step.source_references),
            }
            for step in recipe.steps
        ],
    }
