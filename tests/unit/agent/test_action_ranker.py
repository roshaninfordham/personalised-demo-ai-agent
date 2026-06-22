from pathlib import Path


def test_action_ranker_executable_tests_are_in_browser_runtime_suite() -> None:
    test_path = Path("services/browser_runtime/tests/actionRanker.test.ts")
    source_path = Path("services/browser_runtime/src/actions/actionRanker.ts")

    assert test_path.exists()
    assert "rankActionsForIntent" in source_path.read_text()
    assert (
        "safety" not in test_path.read_text().lower() or "Delete Project" in test_path.read_text()
    )
