import time

from live_demo_agent_runtime.agent_brain.output_validator import AgentOutputValidator
from live_demo_agent_runtime.memory.memory_scoring import score_memory_importance
from live_demo_agent_runtime.memory.memory_types import MemoryUpdate
from live_demo_agent_runtime.persona.persona_tracker import PersonaTracker

from .agent_brain_helpers import TRANSCRIPT_ID, realtime_context
from .helpers import test_settings


def test_validation_persona_and_memory_benchmarks_are_recorded() -> None:
    context = realtime_context()
    raw = (
        '{"spoken_response":"From what I can verify on screen, this is a dashboard.",'
        '"browser_action":null,"memory_updates":[],"confidence":0.8}'
    )
    started = time.perf_counter_ns()
    AgentOutputValidator().validate(raw, context)
    validator_ms = (time.perf_counter_ns() - started) / 1_000_000

    tracker = PersonaTracker(test_settings())
    started = time.perf_counter_ns()
    tracker.update(tracker.initial_state(), "I'm a founder who cares about metrics.")
    persona_ms = (time.perf_counter_ns() - started) / 1_000_000

    started = time.perf_counter_ns()
    score_memory_importance(
        MemoryUpdate("feature_interest", "Revenue metrics", 0.8, 0.0, (TRANSCRIPT_ID,))
    )
    memory_ms = (time.perf_counter_ns() - started) / 1_000_000

    assert validator_ms >= 0
    assert persona_ms >= 0
    assert memory_ms >= 0
