"""Static phase policy descriptions."""

from dataclasses import dataclass

from live_demo_agent_runtime.planner.demo_phase import DemoPhase


@dataclass(frozen=True, slots=True)
class PhasePolicy:
    goal: str
    preferred_tools: tuple[str, ...]
    fallback_behavior: str


PHASE_POLICIES: dict[DemoPhase, PhasePolicy] = {
    DemoPhase.START: PhasePolicy("Greet and orient user.", (), "Ask one short question."),
    DemoPhase.DISCOVERY: PhasePolicy("Learn role and intent.", (), "Avoid interrogation."),
    DemoPhase.OVERVIEW: PhasePolicy(
        "Explain current visible screen.",
        ("highlight_element", "read_current_screen"),
        "Use visible facts only.",
    ),
    DemoPhase.CORE_WORKFLOW: PhasePolicy(
        "Show primary workflow.",
        ("click_element", "highlight_element"),
        "Return to overview if unsafe.",
    ),
    DemoPhase.DEEP_DIVE: PhasePolicy(
        "Explore user-requested area.",
        ("click_element", "search_product_knowledge"),
        "Answer with uncertainty if not grounded.",
    ),
    DemoPhase.Q_AND_A: PhasePolicy(
        "Answer a user question.",
        ("search_product_knowledge", "read_current_screen"),
        "Say cannot verify when unsupported.",
    ),
    DemoPhase.SUMMARY: PhasePolicy("Recap and ask next step.", (), "Avoid risky actions."),
    DemoPhase.END: PhasePolicy("End the demo.", (), "Stop cleanly."),
    DemoPhase.RECOVERY: PhasePolicy(
        "Recover from failed action or unknown screen.",
        ("read_current_screen", "go_back"),
        "Ask a clarifying question.",
    ),
}
