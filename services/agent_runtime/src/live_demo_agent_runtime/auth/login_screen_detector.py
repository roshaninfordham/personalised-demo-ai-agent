"""Deterministic login-screen detection for agent decision making."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_AUTH_PATH_RE = re.compile(r"/(login|log-in|signin|sign-in|auth)(/|$)", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b(email|e-mail|username|user name)\b", re.IGNORECASE)
_PASSWORD_RE = re.compile(r"\b(password|passcode)\b", re.IGNORECASE)
_SIGN_IN_RE = re.compile(r"\b(sign in|signin|log in|login)\b", re.IGNORECASE)
_SIGN_UP_RE = re.compile(r"\b(sign up|signup|create account|register)\b", re.IGNORECASE)


@dataclass(frozen=True)
class LoginScreenDetection:
    login_required: bool
    confidence: float
    detected_fields: tuple[str, ...]
    detected_actions: tuple[str, ...]
    safe_options: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "login_required": self.login_required,
            "confidence": self.confidence,
            "detected_fields": list(self.detected_fields),
            "detected_actions": list(self.detected_actions),
            "safe_options": list(self.safe_options),
            "reason_codes": list(self.reason_codes),
        }


def detect_login_screen(screen: dict[str, Any]) -> LoginScreenDetection:
    """Detect whether the current real screen is an authentication boundary.

    The detector intentionally avoids model calls. It only uses bounded screen metadata,
    visible text, and extracted element labels/types.
    """

    url = str(screen.get("url") or screen.get("final_url") or "")
    title = str(screen.get("title") or "")
    visible_text = str(screen.get("visible_text") or screen.get("summary") or "")
    elements = screen.get("elements") if isinstance(screen.get("elements"), list) else []

    fields: set[str] = set()
    actions: set[str] = set()
    reasons: set[str] = set()

    haystack = " ".join([url, title, visible_text])
    if _AUTH_PATH_RE.search(url):
        reasons.add("auth_url_path")
    if _PASSWORD_RE.search(haystack):
        fields.add("password")
        reasons.add("password_text")
    if _EMAIL_RE.search(haystack):
        fields.add("email")
        reasons.add("email_text")
    if _SIGN_IN_RE.search(haystack):
        actions.add("sign_in")
        reasons.add("sign_in_text")
    if _SIGN_UP_RE.search(haystack):
        actions.add("sign_up")
        reasons.add("sign_up_text")

    for element in elements:
        if not isinstance(element, dict):
            continue
        label = " ".join(
            str(element.get(key) or "") for key in ("label", "text", "role", "input_type")
        )
        input_type = str(element.get("input_type") or "").lower()
        if input_type == "password" or _PASSWORD_RE.search(label):
            fields.add("password")
            reasons.add("password_input")
        if input_type in {"email", "text"} and _EMAIL_RE.search(label):
            fields.add("email")
            reasons.add("email_input")
        if _SIGN_IN_RE.search(label):
            actions.add("sign_in")
            reasons.add("sign_in_action")
        if _SIGN_UP_RE.search(label):
            actions.add("sign_up")
            reasons.add("sign_up_action")

    score = 0.0
    if "password" in fields:
        score += 0.5
    if "sign_in" in actions:
        score += 0.25
    if "email" in fields:
        score += 0.1
    if "sign_up" in actions:
        score += 0.05
    if "auth_url_path" in reasons:
        score += 0.1
    confidence = min(1.0, score)
    login_required = confidence >= 0.55

    safe_options = ["explain_screen"]
    if login_required:
        safe_options.extend(["user_takeover_login"])
        if "sign_up" in actions:
            safe_options.append("open_sign_up_with_confirmation")

    return LoginScreenDetection(
        login_required=login_required,
        confidence=round(confidence, 2),
        detected_fields=tuple(sorted(fields)),
        detected_actions=tuple(sorted(actions)),
        safe_options=tuple(safe_options),
        reason_codes=tuple(sorted(reasons)),
    )
