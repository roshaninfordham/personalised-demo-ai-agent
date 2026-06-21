"""Safe exploration policy."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from live_demo_learner_worker.browser.browser_runtime_client import SafeAction

DANGEROUS_WORDS = {
    "delete",
    "remove",
    "billing",
    "payment",
    "invite",
    "send",
    "publish",
    "upgrade",
    "account settings",
}


@dataclass(frozen=True, slots=True)
class ExplorationPolicy:
    only_low_risk_actions: bool = True
    allow_form_submit: bool = False
    allow_typing: bool = False
    allow_external_navigation: bool = False
    allowed_domains: tuple[str, ...] = ()

    def is_allowed(self, action: SafeAction) -> bool:
        label = action.label.lower()
        if any(word in label for word in DANGEROUS_WORDS):
            return False
        if action.risk_level in {"high", "blocked"}:
            return False
        if self.only_low_risk_actions and action.risk_level != "low":
            return False
        if action.action_type in {"submit_form", "form_submit"} and not self.allow_form_submit:
            return False
        if action.action_type in {"type_demo_text", "type_into_element"} and not self.allow_typing:
            return False
        if action.target_url and not self.allow_external_navigation:
            return _domain_allowed(action.target_url, self.allowed_domains)
        return True


def _domain_allowed(url: str, allowed_domains: tuple[str, ...]) -> bool:
    if not allowed_domains:
        return False
    host = (urlsplit(url).hostname or "").lower().rstrip(".")
    for allowed in allowed_domains:
        normalized = allowed.lower().rstrip(".")
        if normalized.startswith("*."):
            suffix = normalized[1:]
            if host.endswith(suffix) and host != normalized[2:]:
                return True
        elif host == normalized:
            return True
    return False
