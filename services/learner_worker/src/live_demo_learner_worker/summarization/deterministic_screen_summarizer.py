"""Deterministic first-screen summarizer."""

from __future__ import annotations

from live_demo_learner_worker.summarization.evidence_builder import (
    action_labels,
    capability_labels,
    compact_visible_text,
    heading_candidates,
)
from live_demo_learner_worker.summarization.screen_summary_types import (
    FirstScreenSummaryInput,
    ScreenSummary,
)

RISK_WORDS = {"billing", "payment", "delete", "remove", "account settings", "invite", "upgrade"}


class DeterministicScreenSummarizer:
    def summarize(self, input_data: FirstScreenSummaryInput) -> ScreenSummary:
        screen = input_data.screen_state
        visible = compact_visible_text(input_data.visible_text)
        headings = heading_candidates(visible, screen.title)
        capabilities = capability_labels(input_data.ui_elements)
        labels = action_labels(input_data.safe_actions)
        screen_type = _screen_type(screen.title, visible, labels)
        risk_flags = tuple(sorted(word for word in RISK_WORDS if word in visible.lower()))
        unknowns: tuple[str, ...] = () if visible or screen.title else ("visible screen text",)
        element_count = len(input_data.ui_elements)
        summary = (
            f"The page title is '{screen.title or 'unknown'}'. "
            f"The visible screen contains {element_count} observed elements"
        )
        if headings:
            summary += f" and headings including {', '.join(headings[:3])}"
        if labels:
            summary += f". Safe actions include {', '.join(labels[:5])}"
        if risk_flags:
            summary += f". Risk-sensitive areas mentioned: {', '.join(risk_flags)}"
        summary += "."
        confidence = _confidence(input_data, element_count)
        return ScreenSummary(
            screen_id=screen.screen_id,
            summary=summary,
            screen_type=screen_type,
            visible_capabilities=capabilities,
            safe_action_labels=labels,
            unknowns=unknowns,
            confidence=confidence,
            sources=("screen_state", "ui_elements", "safe_actions"),
            metadata={"risk_flags": risk_flags, "visible_text_chars": len(visible)},
        )


def _confidence(input_data: FirstScreenSummaryInput, element_count: int) -> float:
    screen = input_data.screen_state
    title_present = 1.0 if screen.title else 0.0
    visible_text_present = 1.0 if input_data.visible_text else 0.0
    interactive_elements_present = min(1.0, element_count / 5)
    dom_summary_present = 1.0 if screen.dom_summary else 0.0
    accessibility_present = 1.0 if screen.accessibility_summary else 0.0
    safe_actions_present = min(1.0, len(input_data.safe_actions) / 3)
    return round(
        0.25 * title_present
        + 0.20 * visible_text_present
        + 0.20 * interactive_elements_present
        + 0.15 * dom_summary_present
        + 0.10 * accessibility_present
        + 0.10 * safe_actions_present,
        3,
    )


def _screen_type(title: str | None, visible_text: str, labels: tuple[str, ...]) -> str:
    haystack = " ".join([title or "", visible_text, " ".join(labels)]).lower()
    if any(word in haystack for word in ("billing", "payment", "settings", "account")):
        return "settings_or_risky"
    if any(word in haystack for word in ("dashboard", "metrics", "kpi", "analytics")):
        return "dashboard_or_overview"
    if any(word in haystack for word in ("login", "sign in", "password")):
        return "login"
    if any(word in haystack for word in ("report", "chart", "table")):
        return "report"
    if any(word in haystack for word in ("create", "new", "form", "add")):
        return "form"
    return "unknown"
