from __future__ import annotations

from dataclasses import dataclass

from live_demo_backend_common.policy.text_matching import PhraseTrie, normalize_text


@dataclass(frozen=True, slots=True)
class ActionPattern:
    action_type: str
    label_pattern: str
    risk_level_max: str = "medium"


@dataclass(frozen=True, slots=True)
class FormFieldPattern:
    field_label_pattern: str
    field_type: str
    max_chars: int


@dataclass(frozen=True, slots=True)
class ConfirmationPattern:
    action_type: str
    label_pattern: str
    reason: str


@dataclass(frozen=True, slots=True)
class CompiledRecipePolicy:
    allowed_actions: tuple[ActionPattern, ...]
    never_click: tuple[str, ...]
    allowed_domains: tuple[str, ...]
    allowed_form_fields: tuple[FormFieldPattern, ...]
    confirmation_required_actions: tuple[ConfirmationPattern, ...]
    never_click_matcher: PhraseTrie

    def allows_action(self, action_type: str, label: str) -> bool:
        if not self.allowed_actions:
            return True
        normalized = normalize_text(label)
        return any(
            pattern.action_type == action_type
            and normalize_text(pattern.label_pattern) in normalized
            for pattern in self.allowed_actions
        )

    def allows_form_field(self, label: str, field_type: str) -> bool:
        normalized = normalize_text(label)
        return any(
            pattern.field_type == field_type
            and normalize_text(pattern.field_label_pattern) in normalized
            for pattern in self.allowed_form_fields
        )

    def requires_confirmation(self, action_type: str, label: str) -> bool:
        normalized = normalize_text(label)
        return any(
            pattern.action_type == action_type
            and normalize_text(pattern.label_pattern) in normalized
            for pattern in self.confirmation_required_actions
        )


def compile_recipe_policy(raw: dict[str, object] | None) -> CompiledRecipePolicy:
    raw = raw or {}
    allowed_actions = tuple(
        ActionPattern(
            action_type=str(item.get("action_type", "")),
            label_pattern=str(item.get("label_pattern", "")),
            risk_level_max=str(item.get("risk_level_max", "medium")),
        )
        for item in _objects(raw.get("allowed_actions"))[:100]
    )
    never_click = tuple(str(item) for item in _strings(raw.get("never_click"))[:100])
    allowed_domains = tuple(str(item) for item in _strings(raw.get("allowed_domains"))[:50])
    allowed_form_fields = tuple(
        FormFieldPattern(
            field_label_pattern=str(item.get("field_label_pattern", "")),
            field_type=str(item.get("field_type", "text")),
            max_chars=_int_value(item.get("max_chars"), 120),
        )
        for item in _objects(raw.get("allowed_form_fields"))[:100]
    )
    confirmation_required_actions = tuple(
        ConfirmationPattern(
            action_type=str(item.get("action_type", "")),
            label_pattern=str(item.get("label_pattern", "")),
            reason=str(item.get("reason", "")),
        )
        for item in _objects(raw.get("confirmation_required_actions"))[:100]
    )
    return CompiledRecipePolicy(
        allowed_actions=allowed_actions,
        never_click=never_click,
        allowed_domains=allowed_domains,
        allowed_form_fields=allowed_form_fields,
        confirmation_required_actions=confirmation_required_actions,
        never_click_matcher=PhraseTrie(
            [(phrase, "recipe_never_click", "recipe_never_click") for phrase in never_click]
        ),
    )


def _objects(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _int_value(value: object, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return default
