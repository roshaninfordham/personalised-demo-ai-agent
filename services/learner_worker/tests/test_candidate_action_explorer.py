from __future__ import annotations

import pytest

from live_demo_learner_worker.browser.browser_runtime_client import (
    FakeBrowserRuntimeClient,
    SafeAction,
    make_fixture_screen,
)
from live_demo_learner_worker.exploration.candidate_action_explorer import CandidateActionExplorer
from live_demo_learner_worker.exploration.exploration_limits import ExplorationLimits
from live_demo_learner_worker.exploration.exploration_policy import ExplorationPolicy


@pytest.mark.asyncio
async def test_delete_action_skipped() -> None:
    screen = make_fixture_screen()
    risky = SafeAction("act_delete", "click_element", "Delete Project", risk_level="blocked")
    start = type(screen)(screen.screen_state, screen.ui_elements, (*screen.safe_actions, risky))
    explorer = CandidateActionExplorer(
        FakeBrowserRuntimeClient([start]),
        ExplorationPolicy(),
        ExplorationLimits(max_total_actions=5),
    )

    outcome = await explorer.explore(start)

    assert outcome.skipped >= 1
    assert "act_delete" not in FakeBrowserRuntimeClient([start]).executed_actions
