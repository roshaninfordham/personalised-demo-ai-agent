from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine
from live_demo_backend_common.policy.text_matching import normalize_text
from live_demo_backend_common.recipes.recipe_defaults import DEFAULT_NEVER_CLICK
from live_demo_backend_common.recipes.recipe_types import (
    DemoRecipe,
    RecipeEngineLimits,
    RecipeValidationIssue,
)

FORBIDDEN_ACTION_STRINGS = (
    "delete",
    "remove",
    "billing",
    "payment",
    "purchase",
    "checkout",
    "invite",
    "send",
    "publish",
    "upgrade",
    "account settings",
    "api key",
    "token",
    "password",
    "secret",
)

FORBIDDEN_SELECTOR_PATTERNS = (
    "queryselector",
    "getelementbyid",
    "document.",
    "window.",
    "xpath",
    ":nth-",
)

SENSITIVE_FORM_FIELD_WORDS = (
    "password",
    "token",
    "api key",
    "secret",
    "private key",
    "credit card",
    "card number",
    "cvv",
    "ssn",
    "social security",
    "bank account",
    "routing number",
)

STEP_SEQUENCE_ORDER = {
    "START": 0,
    "DISCOVERY": 1,
    "OVERVIEW": 2,
    "CORE_WORKFLOW": 3,
    "DEEP_DIVE": 4,
    "Q_AND_A": 5,
    "SUMMARY": 6,
    "END": 7,
    "RECOVERY": 8,
}


class RecipeSemanticValidator:
    def __init__(
        self,
        *,
        limits: RecipeEngineLimits | None = None,
        redaction_engine: RedactionEngine | None = None,
        allow_local_domains: bool = False,
    ) -> None:
        self._limits = limits or RecipeEngineLimits()
        self._redaction = redaction_engine or RedactionEngine()
        self._allow_local_domains = allow_local_domains

    def validate(self, recipe: DemoRecipe) -> tuple[RecipeValidationIssue, ...]:
        errors: list[RecipeValidationIssue] = []
        errors.extend(_validate_step_order(recipe))
        errors.extend(_validate_phase_sequence(recipe))
        errors.extend(self._validate_recipe_text(recipe))
        errors.extend(self._validate_domains(recipe))
        errors.extend(_validate_actions(recipe))
        errors.extend(_validate_form_fields(recipe))
        errors.extend(_validate_confirmation_actions(recipe))
        return tuple(sorted(errors, key=lambda item: (item.path, item.severity, item.code)))

    def _validate_recipe_text(self, recipe: DemoRecipe) -> list[RecipeValidationIssue]:
        issues: list[RecipeValidationIssue] = []
        fields = {
            "recipe_name": recipe.recipe_name,
            "target_persona": recipe.target_persona,
            "demo_goal": recipe.demo_goal,
            "global_talk_track": recipe.global_talk_track,
        }
        for index, never_click in enumerate(recipe.never_click):
            fields[f"never_click[{index}]"] = never_click
        for index, step in enumerate(recipe.steps):
            fields[f"steps[{index}].goal"] = step.goal
            fields[f"steps[{index}].screen_hint"] = step.screen_hint
            fields[f"steps[{index}].click_hint"] = step.click_hint
            fields[f"steps[{index}].talk_track"] = step.talk_track
            fields[f"steps[{index}].fallback_strategy"] = step.fallback_strategy
            for criterion_index, criterion in enumerate(step.success_criteria):
                fields[f"steps[{index}].success_criteria[{criterion_index}]"] = criterion

        for path, value in fields.items():
            if not value:
                continue
            lowered = value.lower()
            if _contains_javascript(lowered):
                issues.append(
                    RecipeValidationIssue(
                        path=path,
                        code="javascript_forbidden",
                        message="Recipe text must not contain JavaScript instructions.",
                    )
                )
            if path.endswith("click_hint") and _contains_raw_selector(value):
                issues.append(
                    RecipeValidationIssue(
                        path=path,
                        code="raw_selector_forbidden",
                        message="Click hints must not contain raw CSS or XPath selector authority.",
                    )
                )
            redacted = self._redaction.redact_text(value, RedactionContext.PROMPT)
            sensitive_findings = [
                finding
                for finding in redacted.findings
                if finding.finding_type != "high_entropy_secret" or " " not in value.strip()
            ]
            if sensitive_findings:
                issues.append(
                    RecipeValidationIssue(
                        path=path,
                        code="secret_like_text",
                        message="Recipe text contains secret-like or sensitive data.",
                    )
                )
        return issues

    def _validate_domains(self, recipe: DemoRecipe) -> list[RecipeValidationIssue]:
        issues: list[RecipeValidationIssue] = []
        for index, domain in enumerate(recipe.allowed_domains):
            normalized = domain.strip().lower().rstrip(".")
            if not normalized or "/" in normalized or "@" in normalized:
                issues.append(
                    RecipeValidationIssue(
                        path=f"allowed_domains[{index}]",
                        code="invalid_domain_pattern",
                        message="Allowed domain must be a hostname or wildcard hostname.",
                    )
                )
                continue
            host = normalized[2:] if normalized.startswith("*.") else normalized
            if _private_or_local(host) and not self._allow_local_domains:
                issues.append(
                    RecipeValidationIssue(
                        path=f"allowed_domains[{index}]",
                        code="private_domain_forbidden",
                        message="Private, localhost, or link-local domains are not allowed.",
                    )
                )
        return issues


def _validate_step_order(recipe: DemoRecipe) -> list[RecipeValidationIssue]:
    issues: list[RecipeValidationIssue] = []
    orders: dict[int, int] = {}
    keys: dict[str, int] = {}
    for index, step in enumerate(recipe.steps):
        if step.step_order in orders:
            issues.append(
                RecipeValidationIssue(
                    path=f"steps[{index}].step_order",
                    code="duplicate_step_order",
                    message="Step order values must be unique.",
                )
            )
        orders[step.step_order] = index
        if step.step_key in keys:
            issues.append(
                RecipeValidationIssue(
                    path=f"steps[{index}].step_key",
                    code="duplicate_step_key",
                    message="Step keys must be unique.",
                )
            )
        keys[step.step_key] = index
    expected = set(range(len(recipe.steps)))
    if set(orders) != expected:
        issues.append(
            RecipeValidationIssue(
                path="steps",
                code="step_order_not_contiguous",
                message=f"Step order must be contiguous from 0 to {max(len(recipe.steps) - 1, 0)}.",
            )
        )
    return issues


def _validate_phase_sequence(recipe: DemoRecipe) -> list[RecipeValidationIssue]:
    issues: list[RecipeValidationIssue] = []
    last_non_recovery = -1
    for index, step in enumerate(sorted(recipe.steps, key=lambda item: item.step_order)):
        if step.phase is None or step.phase == "RECOVERY":
            continue
        order = STEP_SEQUENCE_ORDER[step.phase]
        if order < last_non_recovery and step.phase in {"START", "DISCOVERY", "OVERVIEW"}:
            issues.append(
                RecipeValidationIssue(
                    path=f"steps[{index}].phase",
                    code="phase_sequence_unreasonable",
                    message="Early demo phases must not appear after later workflow phases.",
                )
            )
        last_non_recovery = max(last_non_recovery, order)
    return issues


def _validate_actions(recipe: DemoRecipe) -> list[RecipeValidationIssue]:
    issues: list[RecipeValidationIssue] = []
    for index, step in enumerate(recipe.steps):
        for action_index, action in enumerate(step.allowed_actions):
            normalized = normalize_text(action)
            if any(word in normalized for word in FORBIDDEN_ACTION_STRINGS):
                issues.append(
                    RecipeValidationIssue(
                        path=f"steps[{index}].allowed_actions[{action_index}]",
                        code="destructive_action_forbidden",
                        message="Allowed actions cannot include destructive or high-risk actions.",
                    )
                )
            if _contains_raw_selector(action):
                issues.append(
                    RecipeValidationIssue(
                        path=f"steps[{index}].allowed_actions[{action_index}]",
                        code="raw_selector_forbidden",
                        message="Allowed actions must name tools, not raw selectors.",
                    )
                )
            if _contains_javascript(action.lower()):
                issues.append(
                    RecipeValidationIssue(
                        path=f"steps[{index}].allowed_actions[{action_index}]",
                        code="javascript_forbidden",
                        message="Allowed actions must not contain JavaScript.",
                    )
                )
    for index, value in enumerate(recipe.never_click):
        if len(value) > 100:
            issues.append(
                RecipeValidationIssue(
                    path=f"never_click[{index}]",
                    code="never_click_too_long",
                    message="Never-click entries must be at most 100 characters.",
                )
            )
    missing_defaults = {item.lower() for item in DEFAULT_NEVER_CLICK} - {
        item.lower() for item in recipe.never_click
    }
    if missing_defaults:
        issues.append(
            RecipeValidationIssue(
                path="never_click",
                code="default_never_click_missing",
                message="Default never-click restrictions must be present after defaults.",
            )
        )
    return issues


def _validate_form_fields(recipe: DemoRecipe) -> list[RecipeValidationIssue]:
    issues: list[RecipeValidationIssue] = []
    for index, field in enumerate(recipe.allowed_form_fields):
        combined = normalize_text(f"{field.field_label_pattern} {field.field_type}")
        if any(word in combined for word in SENSITIVE_FORM_FIELD_WORDS):
            issues.append(
                RecipeValidationIssue(
                    path=f"allowed_form_fields[{index}]",
                    code="sensitive_form_field_forbidden",
                    message=(
                        "Recipe form fields cannot allow password, token, secret, "
                        "or payment fields."
                    ),
                )
            )
        if field.max_chars <= 0 or field.max_chars > 2000:
            issues.append(
                RecipeValidationIssue(
                    path=f"allowed_form_fields[{index}].max_chars",
                    code="invalid_field_max_chars",
                    message="Allowed form field max_chars must be between 1 and 2000.",
                )
            )
    return issues


def _validate_confirmation_actions(recipe: DemoRecipe) -> list[RecipeValidationIssue]:
    issues: list[RecipeValidationIssue] = []
    for index, item in enumerate(recipe.confirmation_required_actions):
        combined = normalize_text(f"{item.action_type} {item.label_pattern}")
        if any(word in combined for word in ("delete", "remove", "payment", "billing")):
            issues.append(
                RecipeValidationIssue(
                    path=f"confirmation_required_actions[{index}]",
                    code="globally_blocked_confirmation_forbidden",
                    message="Confirmation cannot enable globally blocked actions.",
                )
            )
    return issues


def _contains_javascript(value: str) -> bool:
    return any(marker in value for marker in ("document.", "window.", "javascript:", "<script"))


def _contains_raw_selector(value: str) -> bool:
    lowered = value.lower()
    if any(marker in lowered for marker in FORBIDDEN_SELECTOR_PATTERNS):
        return True
    return bool(re.search(r"(^|\s)(#[a-z0-9_-]+|[a-z0-9_-]*\.[a-z0-9_-]+|\[[^\]]+\]|>)", lowered))


def _private_or_local(host: str) -> bool:
    if host == "localhost":
        return True
    parsed = urlsplit(f"https://{host}")
    candidate = parsed.hostname or host
    try:
        ip = ipaddress.ip_address(candidate)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified
