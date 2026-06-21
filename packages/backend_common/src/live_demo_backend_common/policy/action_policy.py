from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from live_demo_backend_common.policy.domain_policy import domain_allowed
from live_demo_backend_common.policy.policy_types import (
    ConfirmationContext,
    MatchedPolicyRule,
    PolicyActor,
    PolicyDecision,
    PolicyResource,
)
from live_demo_backend_common.policy.recipe_policy import CompiledRecipePolicy
from live_demo_backend_common.policy.text_matching import PhraseTrie, normalize_text
from live_demo_policies.action_safety_rules import ACTION_SAFETY_RULES

MAX_POLICY_TEXT_CHARS = 8000
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "blocked": 3, "unknown": 4}
_CATEGORIES = cast(list[dict[str, object]], ACTION_SAFETY_RULES["categories"])
_FORBIDDEN_AUTHORITY = cast(
    dict[str, list[str]],
    ACTION_SAFETY_RULES["forbidden_authority"],
)
_WEIGHTS = cast(dict[str, float], ACTION_SAFETY_RULES["weights"])
_SENSITIVE_FIELD_PHRASES = cast(list[str], ACTION_SAFETY_RULES["sensitive_field_phrases"])


@dataclass(frozen=True, slots=True)
class ActionPolicyRequest:
    organization_id: UUID
    session_id: UUID | None
    actor: PolicyActor
    action_type: str
    action_label: str | None = None
    element_role: str | None = None
    element_label: str | None = None
    element_text: str | None = None
    surrounding_text: str | None = None
    input_type: str | None = None
    current_url: str | None = None
    target_url: str | None = None
    risk_context: dict[str, str] | None = None
    recipe_policy: CompiledRecipePolicy | None = None
    confirmation: ConfirmationContext | None = None
    trace_id: str = ""


class ActionSafetyPolicy:
    def __init__(self) -> None:
        phrases: list[tuple[str, str, str]] = []
        self._categories: dict[str, dict[str, object]] = {}
        for category in _CATEGORIES:
            category_name = str(category["category"])
            self._categories[category_name] = category
            phrases.extend(
                (str(phrase), category_name, category_name)
                for phrase in cast(list[str], category["phrases"])
            )
        self._matcher = PhraseTrie(phrases)
        self._js_markers = tuple(
            marker.lower() for marker in _FORBIDDEN_AUTHORITY["javascript_markers"]
        )
        self._selector_markers = tuple(
            marker.lower() for marker in _FORBIDDEN_AUTHORITY["selector_markers"]
        )

    def evaluate(self, request: ActionPolicyRequest) -> PolicyDecision:
        reason_codes: list[str] = []
        matched_rules: list[MatchedPolicyRule] = []
        combined = _combined_text(request)
        normalized = normalize_text(combined)
        if len(combined) > MAX_POLICY_TEXT_CHARS:
            reason_codes.append("policy_text_truncated")
            combined = combined[:MAX_POLICY_TEXT_CHARS]
        if any(marker in combined.lower() for marker in self._js_markers):
            return _decision(request, "blocked", "blocked", 1.0, ["javascript_forbidden"], [])
        if any(marker in combined.lower() for marker in self._selector_markers):
            return _decision(request, "blocked", "blocked", 1.0, ["raw_selector_forbidden"], [])

        matches = self._matcher.match(combined)
        matched_rules.extend(matches)
        categories = {match.category for match in matches}
        if "blocked_destructive" in categories:
            return _decision(
                request,
                "blocked",
                "blocked",
                1.0,
                ["blocked_destructive_action"],
                matched_rules,
            )
        if "payment_billing" in categories:
            return _decision(
                request,
                "blocked",
                "blocked",
                1.0,
                ["payment_billing_blocked"],
                matched_rules,
            )

        recipe = request.recipe_policy
        if recipe is not None:
            recipe_match = recipe.never_click_matcher.match(combined)
            if recipe_match:
                return _decision(
                    request,
                    "blocked",
                    "blocked",
                    1.0,
                    ["recipe_never_click_match"],
                    recipe_match,
                )
            if recipe.requires_confirmation(request.action_type, normalized):
                reason_codes.append("recipe_confirmation_required")

        if request.target_url:
            allowed_domains = recipe.allowed_domains if recipe else ()
            if not domain_allowed(request.target_url, allowed_domains):
                return _decision(
                    request,
                    "blocked",
                    "blocked",
                    1.0,
                    ["domain_not_allowed", "external_navigation_blocked"],
                    matched_rules,
                )

        if _sensitive_field(request):
            return _decision(
                request,
                "blocked",
                "blocked",
                1.0,
                ["sensitive_field_blocked"],
                matched_rules,
            )

        risk_score = _risk_score(categories, request, recipe)
        risk_level = _risk_level(risk_score)
        if "communication_side_effect" in categories or "account_settings" in categories:
            risk_level = "high"
            risk_score = max(risk_score, 0.7)
        if risk_level == "high" or "recipe_confirmation_required" in reason_codes:
            if request.confirmation is None or not request.confirmation.confirmed:
                return _decision(
                    request,
                    "confirmation_required",
                    "high",
                    risk_score,
                    [*reason_codes, "high_risk_requires_confirmation"],
                    matched_rules,
                )
            reason_codes.append("confirmation_token_valid")
        if request.action_type in {"read_current_screen", "highlight_element"}:
            reason_codes.append("safe_read_action")
            risk_level = "low"
            risk_score = min(risk_score, 0.1)
        elif not reason_codes:
            reason_codes.append("safe_action_allowed")
        return _decision(request, "allowed", risk_level, risk_score, reason_codes, matched_rules)


def _combined_text(request: ActionPolicyRequest) -> str:
    return " ".join(
        value or ""
        for value in (
            request.action_type,
            request.action_label,
            request.element_role,
            request.element_label,
            request.element_text,
            request.surrounding_text,
            request.input_type,
            request.current_url,
            request.target_url,
            " ".join((request.risk_context or {}).values()),
        )
    )


def _risk_score(
    categories: set[str],
    request: ActionPolicyRequest,
    recipe: CompiledRecipePolicy | None,
) -> float:
    label_risk = 0.75 if categories & {"communication_side_effect", "account_settings"} else 0.2
    if categories & {"medium_form_action"}:
        label_risk = 0.45
    if categories & {"low_navigation"}:
        label_risk = 0.05
    role_risk = 0.35 if request.element_role in {"input", "textarea", "select"} else 0.15
    context_risk = label_risk
    recipe_allows = recipe is None or recipe.allows_action(
        request.action_type,
        _combined_text(request),
    )
    recipe_risk = 0.0 if recipe_allows else 0.35
    domain_risk = 0.0 if request.target_url is None else 0.2
    field_risk = 1.0 if _sensitive_field(request) else 0.1
    actor_risk = 0.0 if request.actor.role in {"owner", "admin"} else 0.1
    return max(
        0.0,
        min(
            1.0,
            float(_WEIGHTS["label"]) * label_risk
            + float(_WEIGHTS["role"]) * role_risk
            + float(_WEIGHTS["context"]) * context_risk
            + float(_WEIGHTS["recipe"]) * recipe_risk
            + float(_WEIGHTS["domain"]) * domain_risk
            + float(_WEIGHTS["field"]) * field_risk
            + float(_WEIGHTS["actor"]) * actor_risk,
        ),
    )


def _risk_level(score: float) -> str:
    if score >= 0.85:
        return "blocked"
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _sensitive_field(request: ActionPolicyRequest) -> bool:
    text = normalize_text(" ".join([request.element_label or "", request.input_type or ""]))
    return any(
        phrase in text for phrase in _SENSITIVE_FIELD_PHRASES
    ) or request.input_type == "password"


def _decision(
    request: ActionPolicyRequest,
    decision: str,
    risk_level: str,
    risk_score: float,
    reason_codes: list[str],
    matched_rules: list[MatchedPolicyRule],
) -> PolicyDecision:
    return PolicyDecision.make(
        decision=decision,  # type: ignore[arg-type]
        risk_level=risk_level,  # type: ignore[arg-type]
        risk_score=risk_score,
        requires_confirmation=decision == "confirmation_required",
        reason_codes=reason_codes,
        matched_rules=matched_rules,
        actor=request.actor,
        resource=PolicyResource("browser_action", request.action_label or request.action_type),
        organization_id=request.organization_id,
        session_id=request.session_id,
        trace_id=request.trace_id,
    )
