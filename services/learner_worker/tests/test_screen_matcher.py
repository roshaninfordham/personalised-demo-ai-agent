from __future__ import annotations

from live_demo_learner_worker.browser.browser_runtime_client import make_fixture_screen
from live_demo_learner_worker.matching.screen_matcher import ScreenMatcher


def test_same_screen_matches_high() -> None:
    screen = make_fixture_screen()
    result = ScreenMatcher().match(screen, screen)

    assert result.decision == "matched"
    assert result.similarity_score >= 0.9


def test_different_screen_does_not_match() -> None:
    left = make_fixture_screen(title="Dashboard", visible_text="Dashboard metrics")
    right = make_fixture_screen(screen_hash="login", title="Login", visible_text="Email Password")

    assert ScreenMatcher().match(left, right).decision != "matched"
