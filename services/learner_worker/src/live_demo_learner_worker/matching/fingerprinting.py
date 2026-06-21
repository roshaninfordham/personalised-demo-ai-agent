"""Screen and element fingerprint helpers."""

from __future__ import annotations

import hashlib

from live_demo_learner_worker.browser.browser_runtime_client import BrowserScreenRead, UIElement


def screen_fingerprint(screen: BrowserScreenRead) -> str:
    parts = [
        screen.screen_state.url_path or "",
        screen.screen_state.title or "",
        " ".join(sorted(action.label.lower() for action in screen.safe_actions)),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def element_fingerprint(element: UIElement) -> str:
    if element.element_fingerprint:
        return element.element_fingerprint
    parts = [element.role or "", element.label or "", element.text or ""]
    return hashlib.sha256("|".join(parts).lower().encode()).hexdigest()
