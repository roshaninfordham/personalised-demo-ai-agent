"""Deterministic placeholder voice responder for Phase 7."""


def respond_to_user_transcript(text: str) -> str:
    normalized = text.lower()
    if "dashboard" in normalized:
        return (
            "I heard you ask about the dashboard. "
            "The browser demo planner will handle that in the next phase."
        )
    return "I heard you. The full demo agent brain will connect in a later phase."
