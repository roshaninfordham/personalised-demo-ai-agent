from __future__ import annotations

from urllib.parse import urlsplit

from live_demo_backend_common.policy.domain_policy import DomainMatcher
from live_demo_backend_common.policy.text_matching import normalize_text
from live_demo_backend_common.recipes.recipe_errors import RecipeCompilationError
from live_demo_backend_common.recipes.recipe_hash import compiled_hash, recipe_hash
from live_demo_backend_common.recipes.recipe_normalizer import (
    normalize_tokens,
    normalized_json_size,
)
from live_demo_backend_common.recipes.recipe_types import (
    CompiledAllowedAction,
    CompiledDomainPolicy,
    CompiledFallbackStrategy,
    CompiledRecipe,
    CompiledRecipeSafetyPolicy,
    CompiledRecipeStep,
    CompileRecipeRequest,
)


class RecipeCompiler:
    def __init__(self, *, max_payload_bytes: int = 65_536) -> None:
        self._max_payload_bytes = max_payload_bytes

    def compile(self, request: CompileRecipeRequest) -> CompiledRecipe:
        recipe = request.normalized_recipe
        steps = tuple(
            CompiledRecipeStep(
                step_id=step.step_id,
                step_order=step.step_order,
                step_key=step.step_key,
                phase=step.phase or "OVERVIEW",
                required=step.required,
                goal=step.goal,
                screen_hint_tokens=normalize_tokens(step.screen_hint or step.goal),
                click_hint_tokens=normalize_tokens(step.click_hint),
                talk_track=step.talk_track,
                allowed_tool_names=frozenset(
                    _normalize_tool_name(action) for action in step.allowed_actions
                ),
                success_criteria=step.success_criteria,
                fallback_strategy=step.fallback_strategy
                or (
                    "Read the current screen, explain what can be verified, "
                    "and ask whether to continue."
                ),
                max_attempts=step.max_attempts,
                source_confidence=step.confidence,
            )
            for step in sorted(recipe.steps, key=lambda item: item.step_order)
        )
        step_by_key = {step.step_key: step for step in steps}
        allowed_action_index: dict[str, CompiledAllowedAction] = {}
        for step in recipe.steps:
            for action in step.allowed_actions:
                normalized = _normalize_tool_name(action)
                allowed_action_index[f"{normalized}:{normalize_text(action)}"] = (
                    CompiledAllowedAction(
                        action_type=normalized,
                        label_pattern=action,
                        risk_level_max="medium",
                    )
                )
        domain_matcher = DomainMatcher.compile(
            recipe.allowed_domains or _domain_from_url(request.product_url)
        )
        context_payload = {
            "recipe_name": recipe.recipe_name,
            "target_persona": recipe.target_persona,
            "demo_goal": recipe.demo_goal,
            "global_talk_track": recipe.global_talk_track,
            "steps": [
                {
                    "step_order": step.step_order,
                    "step_key": step.step_key,
                    "phase": step.phase,
                    "goal": step.goal,
                    "talk_track": step.talk_track,
                    "success_criteria": list(step.success_criteria),
                }
                for step in steps
            ],
            "never_click": list(recipe.never_click),
        }
        payload = {
            "recipe_id": str(request.recipe_id),
            "product_id": str(request.product_id),
            "version": request.version,
            "global_policy_version": request.global_policy_version,
            "steps_by_order": [_step_payload(step) for step in steps],
            "safety_policy": {
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
            },
            "allowed_action_index": {
                key: {
                    "action_type": value.action_type,
                    "label_pattern": value.label_pattern,
                    "risk_level_max": value.risk_level_max,
                }
                for key, value in sorted(allowed_action_index.items())
            },
            "never_click_matcher_payload": {"phrases": list(recipe.never_click)},
            "domain_policy": {
                "exact_domains": sorted(domain_matcher.exact),
                "wildcard_suffixes": sorted(domain_matcher.wildcard_suffixes),
            },
            "success_criteria_by_step": {
                step.step_key: list(step.success_criteria) for step in steps
            },
            "fallback_by_step": {
                step.step_key: {
                    "step_key": step.step_key,
                    "strategy": step.fallback_strategy,
                    "max_attempts": step.max_attempts,
                }
                for step in steps
            },
            "context_payload": context_payload,
        }
        if normalized_json_size(payload) > self._max_payload_bytes:
            raise RecipeCompilationError("Compiled recipe exceeds configured payload limit.")
        r_hash = recipe_hash(recipe)
        c_hash = compiled_hash(payload)
        payload["recipe_hash"] = r_hash
        payload["compiled_hash"] = c_hash
        return CompiledRecipe(
            recipe_id=request.recipe_id,
            product_id=request.product_id,
            recipe_hash=r_hash,
            compiled_hash=c_hash,
            version=request.version,
            steps_by_order=steps,
            step_by_key=step_by_key,
            safety_policy=CompiledRecipeSafetyPolicy(
                never_click=recipe.never_click,
                allowed_domains=recipe.allowed_domains,
                allowed_form_fields=recipe.allowed_form_fields,
                confirmation_required_actions=recipe.confirmation_required_actions,
            ),
            allowed_action_index=allowed_action_index,
            never_click_matcher_payload={"phrases": list(recipe.never_click)},
            domain_policy=CompiledDomainPolicy(
                exact_domains=tuple(sorted(domain_matcher.exact)),
                wildcard_suffixes=tuple(sorted(domain_matcher.wildcard_suffixes)),
            ),
            success_criteria_by_step={
                step.step_key: tuple(step.success_criteria) for step in steps
            },
            fallback_by_step={
                step.step_key: CompiledFallbackStrategy(
                    step_key=step.step_key,
                    strategy=step.fallback_strategy,
                    max_attempts=step.max_attempts,
                )
                for step in steps
            },
            context_payload=context_payload,
            payload=payload,
        )


def _step_payload(step: CompiledRecipeStep) -> dict[str, object]:
    return {
        "step_id": str(step.step_id),
        "step_order": step.step_order,
        "step_key": step.step_key,
        "phase": step.phase,
        "required": step.required,
        "goal": step.goal,
        "screen_hint_tokens": sorted(step.screen_hint_tokens),
        "click_hint_tokens": sorted(step.click_hint_tokens),
        "talk_track": step.talk_track,
        "allowed_tool_names": sorted(step.allowed_tool_names),
        "success_criteria": list(step.success_criteria),
        "fallback_strategy": step.fallback_strategy,
        "max_attempts": step.max_attempts,
        "source_confidence": step.source_confidence,
    }


def _normalize_tool_name(value: str) -> str:
    aliases = {"highlight": "highlight_element", "click": "click_element"}
    normalized = normalize_text(value).replace(" ", "_")
    return aliases.get(normalized, normalized)


def _domain_from_url(product_url: str) -> tuple[str, ...]:
    host = urlsplit(product_url).hostname
    return (host.lower().rstrip("."),) if host else ()
