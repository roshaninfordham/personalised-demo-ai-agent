from __future__ import annotations

import re
from typing import Any

from live_demo_backend_common.recipes.recipe_defaults import apply_recipe_defaults
from live_demo_backend_common.recipes.recipe_normalizer import (
    json_depth_and_key_count,
    normalize_optional_text,
    normalized_json_size,
)
from live_demo_backend_common.recipes.recipe_semantic_validator import RecipeSemanticValidator
from live_demo_backend_common.recipes.recipe_types import (
    AllowedFormField,
    ConfirmationRequiredAction,
    DemoRecipe,
    DemoRecipeStep,
    RecipeEngineLimits,
    RecipeValidationIssue,
    RecipeValidationResult,
)

STEP_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,80}$")
VALID_PHASES = {
    "START",
    "DISCOVERY",
    "OVERVIEW",
    "CORE_WORKFLOW",
    "DEEP_DIVE",
    "Q_AND_A",
    "SUMMARY",
    "END",
    "RECOVERY",
}
SAFE_TOOL_NAMES = {
    "read_current_screen",
    "highlight_element",
    "click_element",
    "type_demo_text",
    "scroll",
    "go_back",
    "search_product_knowledge",
    "save_lead_insight",
    # Legacy aliases accepted at the API boundary, normalized by compiler matching.
    "highlight",
    "click",
}


class RecipeValidator:
    def __init__(
        self,
        *,
        limits: RecipeEngineLimits | None = None,
        semantic_validator: RecipeSemanticValidator | None = None,
        product_url: str | None = None,
    ) -> None:
        self._limits = limits or RecipeEngineLimits()
        self._semantic = semantic_validator or RecipeSemanticValidator(limits=self._limits)
        self._product_url = product_url

    def validate(self, raw_recipe: dict[str, Any]) -> RecipeValidationResult:
        errors: list[RecipeValidationIssue] = []
        warnings: list[RecipeValidationIssue] = []
        try:
            size = normalized_json_size(raw_recipe)
        except (TypeError, ValueError):
            return RecipeValidationResult(
                valid=False,
                errors=(
                    RecipeValidationIssue(
                        path="$",
                        code="invalid_json",
                        message="Recipe must be JSON serializable.",
                    ),
                ),
            )
        if size > self._limits.max_json_bytes:
            errors.append(
                RecipeValidationIssue(
                    path="$",
                    code="recipe_json_too_large",
                    message="Recipe JSON exceeds the configured size limit.",
                )
            )
        depth, key_count = json_depth_and_key_count(raw_recipe)
        if depth > self._limits.max_json_depth:
            errors.append(
                RecipeValidationIssue(
                    path="$",
                    code="recipe_json_too_deep",
                    message="Recipe JSON exceeds the configured depth limit.",
                )
            )
        if key_count > self._limits.max_json_keys:
            errors.append(
                RecipeValidationIssue(
                    path="$",
                    code="recipe_json_too_many_keys",
                    message="Recipe JSON exceeds the configured key limit.",
                )
            )

        parsed, structural_errors = self._parse_recipe(raw_recipe)
        errors.extend(structural_errors)
        normalized: DemoRecipe | None = None
        if parsed is not None:
            defaulted = apply_recipe_defaults(parsed, product_url=self._product_url)
            if tuple(parsed.never_click) != tuple(defaulted.never_click):
                warnings.append(
                    RecipeValidationIssue(
                        path="never_click",
                        code="default_never_click_added",
                        message="Default blocked actions were added to never_click.",
                        severity="warning",
                    )
                )
            if tuple(parsed.allowed_domains) != tuple(defaulted.allowed_domains):
                warnings.append(
                    RecipeValidationIssue(
                        path="allowed_domains",
                        code="default_allowed_domain_added",
                        message="Product URL domain was added as the default allowed domain.",
                        severity="warning",
                    )
                )
            errors.extend(self._semantic.validate(defaulted))
            normalized = defaulted if not errors else None

        return RecipeValidationResult(
            valid=not errors,
            errors=tuple(sorted(errors, key=lambda item: (item.path, item.severity, item.code))),
            warnings=tuple(
                sorted(warnings, key=lambda item: (item.path, item.severity, item.code))
            ),
            normalized_recipe=normalized,
        )

    def _parse_recipe(
        self, raw: dict[str, Any]
    ) -> tuple[DemoRecipe | None, list[RecipeValidationIssue]]:
        errors: list[RecipeValidationIssue] = []
        recipe_name = normalize_optional_text(raw.get("recipe_name"))
        target_persona = normalize_optional_text(raw.get("target_persona"))
        demo_goal = normalize_optional_text(raw.get("demo_goal"))
        global_talk_track = normalize_optional_text(raw.get("global_talk_track"))
        if not recipe_name or len(recipe_name) > 200:
            errors.append(
                RecipeValidationIssue(
                    path="recipe_name",
                    code="invalid_recipe_name",
                    message="Recipe name is required and must be at most 200 characters.",
                )
            )
        if target_persona and len(target_persona) > 100:
            errors.append(
                RecipeValidationIssue(
                    path="target_persona",
                    code="text_too_long",
                    message="Target persona must be at most 100 characters.",
                )
            )
        if not demo_goal or len(demo_goal) > self._limits.max_text_field_chars:
            errors.append(
                RecipeValidationIssue(
                    path="demo_goal",
                    code="invalid_demo_goal",
                    message="Demo goal is required and must fit the configured text limit.",
                )
            )
        if global_talk_track and len(global_talk_track) > self._limits.max_text_field_chars:
            errors.append(
                RecipeValidationIssue(
                    path="global_talk_track",
                    code="text_too_long",
                    message="Global talk track exceeds the configured text limit.",
                )
            )

        never_click = _string_list(raw.get("never_click"), "never_click", errors)
        if len(never_click) > self._limits.max_never_click_items:
            errors.append(
                RecipeValidationIssue(
                    path="never_click",
                    code="too_many_never_click_items",
                    message="Never-click list exceeds the configured item limit.",
                )
            )
        allowed_domains = _string_list(raw.get("allowed_domains"), "allowed_domains", errors)
        if len(allowed_domains) > self._limits.max_allowed_domains:
            errors.append(
                RecipeValidationIssue(
                    path="allowed_domains",
                    code="too_many_allowed_domains",
                    message="Allowed domains exceed the configured item limit.",
                )
            )
        form_fields = _parse_form_fields(raw.get("allowed_form_fields"), errors)
        confirmation_actions = _parse_confirmation_actions(
            raw.get("confirmation_required_actions"), errors
        )
        steps = _parse_steps(raw.get("steps"), self._limits, errors)
        if errors:
            return None, errors
        return (
            DemoRecipe(
                recipe_name=recipe_name or "",
                target_persona=target_persona,
                demo_goal=demo_goal or "",
                global_talk_track=global_talk_track,
                never_click=tuple(never_click),
                allowed_domains=tuple(allowed_domains),
                allowed_form_fields=tuple(form_fields),
                confirmation_required_actions=tuple(confirmation_actions),
                steps=tuple(steps),
                status=str(raw.get("status") or "draft"),  # type: ignore[arg-type]
            ),
            [],
        )


def _string_list(
    value: object,
    path: str,
    errors: list[RecipeValidationIssue],
    *,
    max_item_chars: int = 100,
) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(
            RecipeValidationIssue(
                path=path,
                code="invalid_array",
                message="Field must be an array.",
            )
        )
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        text = normalize_optional_text(item)
        if not text or len(text) > max_item_chars:
            errors.append(
                RecipeValidationIssue(
                    path=f"{path}[{index}]",
                    code="invalid_string_item",
                    message=f"Item must be non-empty and at most {max_item_chars} characters.",
                )
            )
        else:
            result.append(text)
    return result


def _parse_form_fields(
    value: object,
    errors: list[RecipeValidationIssue],
) -> list[AllowedFormField]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(
            RecipeValidationIssue("allowed_form_fields", "invalid_array", "Field must be an array.")
        )
        return []
    result: list[AllowedFormField] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(
                RecipeValidationIssue(
                    f"allowed_form_fields[{index}]", "invalid_object", "Item must be an object."
                )
            )
            continue
        label = normalize_optional_text(item.get("field_label_pattern"))
        field_type = normalize_optional_text(item.get("field_type")) or "text"
        max_chars = item.get("max_chars", 120)
        if not label:
            errors.append(
                RecipeValidationIssue(
                    f"allowed_form_fields[{index}].field_label_pattern",
                    "missing_field_label_pattern",
                    "Allowed form field requires a label pattern.",
                )
            )
            continue
        if not isinstance(max_chars, int):
            errors.append(
                RecipeValidationIssue(
                    f"allowed_form_fields[{index}].max_chars",
                    "invalid_max_chars",
                    "max_chars must be an integer.",
                )
            )
            continue
        result.append(AllowedFormField(label, field_type, max_chars))
    return result


def _parse_confirmation_actions(
    value: object,
    errors: list[RecipeValidationIssue],
) -> list[ConfirmationRequiredAction]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(
            RecipeValidationIssue(
                "confirmation_required_actions", "invalid_array", "Field must be an array."
            )
        )
        return []
    result: list[ConfirmationRequiredAction] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(
                RecipeValidationIssue(
                    f"confirmation_required_actions[{index}]",
                    "invalid_object",
                    "Item must be an object.",
                )
            )
            continue
        action_type = normalize_optional_text(item.get("action_type"))
        label = normalize_optional_text(item.get("label_pattern"))
        reason = normalize_optional_text(item.get("reason"))
        if not action_type or not label or not reason:
            errors.append(
                RecipeValidationIssue(
                    f"confirmation_required_actions[{index}]",
                    "missing_confirmation_fields",
                    "Confirmation action requires action_type, label_pattern, and reason.",
                )
            )
            continue
        result.append(ConfirmationRequiredAction(action_type, label, reason))
    return result


def _parse_steps(
    value: object,
    limits: RecipeEngineLimits,
    errors: list[RecipeValidationIssue],
) -> list[DemoRecipeStep]:
    if not isinstance(value, list) or not value:
        errors.append(
            RecipeValidationIssue(
                path="steps",
                code="invalid_step_count",
                message=f"Recipe must contain between 1 and {limits.max_steps} steps.",
            )
        )
        return []
    if len(value) > limits.max_steps:
        errors.append(
            RecipeValidationIssue(
                path="steps",
                code="too_many_steps",
                message=f"Recipe can contain at most {limits.max_steps} steps.",
            )
        )
    steps: list[DemoRecipeStep] = []
    for index, item in enumerate(value[: limits.max_steps]):
        if not isinstance(item, dict):
            errors.append(
                RecipeValidationIssue(
                    f"steps[{index}]", "invalid_object", "Step must be an object."
                )
            )
            continue
        step_order = item.get("step_order")
        step_key = normalize_optional_text(item.get("step_key"))
        goal = normalize_optional_text(item.get("goal"))
        if not isinstance(step_order, int) or step_order < 0:
            errors.append(
                RecipeValidationIssue(
                    f"steps[{index}].step_order",
                    "invalid_step_order",
                    "Step order must be a non-negative integer.",
                )
            )
            step_order = index
        if not step_key or not STEP_KEY_RE.fullmatch(step_key):
            errors.append(
                RecipeValidationIssue(
                    f"steps[{index}].step_key",
                    "invalid_step_key",
                    (
                        "Step key must start with a lowercase letter or number and use "
                        "lowercase letters, numbers, hyphens, or underscores."
                    ),
                )
            )
            step_key = f"step_{index}"
        if not goal or len(goal) > limits.max_text_field_chars:
            errors.append(
                RecipeValidationIssue(
                    f"steps[{index}].goal",
                    "invalid_step_goal",
                    "Step goal is required and must fit the configured text limit.",
                )
            )
            goal = goal or ""
        phase = normalize_optional_text(item.get("phase"))
        if phase is not None and phase not in VALID_PHASES:
            errors.append(
                RecipeValidationIssue(
                    f"steps[{index}].phase",
                    "invalid_phase",
                    "Step phase is not a supported demo phase.",
                )
            )
            phase = None
        allowed_actions = tuple(
            _string_list(
                item.get("allowed_actions"),
                f"steps[{index}].allowed_actions",
                errors,
                max_item_chars=100,
            )
        )
        if len(allowed_actions) > 20:
            errors.append(
                RecipeValidationIssue(
                    f"steps[{index}].allowed_actions",
                    "too_many_step_actions",
                    "Each step can allow at most 20 action names.",
                )
            )
        for action_index, action in enumerate(allowed_actions):
            if action not in SAFE_TOOL_NAMES and " " not in action:
                errors.append(
                    RecipeValidationIssue(
                        f"steps[{index}].allowed_actions[{action_index}]",
                        "unknown_action_name",
                        "Allowed action must be a known safe tool name or descriptive hint.",
                        severity="warning",
                    )
                )
        success_criteria = tuple(
            _string_list(
                item.get("success_criteria"),
                f"steps[{index}].success_criteria",
                errors,
                max_item_chars=300,
            )
        )
        max_attempts = item.get("max_attempts", 2)
        if not isinstance(max_attempts, int) or max_attempts < 0 or max_attempts > 5:
            errors.append(
                RecipeValidationIssue(
                    f"steps[{index}].max_attempts",
                    "invalid_max_attempts",
                    "max_attempts must be between 0 and 5.",
                )
            )
            max_attempts = 2
        required = item.get("required", True)
        if not isinstance(required, bool):
            errors.append(
                RecipeValidationIssue(
                    f"steps[{index}].required",
                    "invalid_required",
                    "required must be a boolean.",
                )
            )
            required = True
        confidence = item.get("confidence", 1.0)
        if not isinstance(confidence, int | float):
            confidence = 1.0
        source_references = tuple(
            _string_list(
                item.get("source_references"),
                f"steps[{index}].source_references",
                errors,
                max_item_chars=200,
            )
        )
        steps.append(
            DemoRecipeStep(
                step_order=step_order,
                step_key=step_key,
                phase=phase,  # type: ignore[arg-type]
                goal=goal,
                screen_hint=normalize_optional_text(item.get("screen_hint")),
                click_hint=normalize_optional_text(item.get("click_hint")),
                talk_track=normalize_optional_text(item.get("talk_track")),
                allowed_actions=allowed_actions[:20],
                success_criteria=success_criteria[:20],
                fallback_strategy=normalize_optional_text(item.get("fallback_strategy")),
                max_attempts=max_attempts,
                required=required,
                confidence=max(0.0, min(1.0, float(confidence))),
                source_references=source_references,
            )
        )
    return steps
