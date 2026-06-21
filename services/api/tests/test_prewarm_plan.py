from live_demo_api.orchestration.prewarm_plan import (
    build_default_prewarm_plan,
    validate_prewarm_plan,
)


def test_prewarm_dag_dependencies_valid() -> None:
    plan = build_default_prewarm_plan()

    assert validate_prewarm_plan(plan) is True
    by_name = {step.name: step for step in plan}
    assert "create_browser_session" in by_name["navigate_browser"].depends_on
    assert "navigate_browser" in by_name["read_first_screen"].depends_on
    assert "load_session" in by_name["enqueue_learner"].depends_on


def test_prewarm_parallel_tasks_depend_only_on_session_load() -> None:
    plan = build_default_prewarm_plan()
    by_name = {step.name: step for step in plan}

    assert by_name["compile_recipe"].depends_on == ("load_session",)
    assert by_name["create_voice_session"].depends_on == ("load_session",)
    assert by_name["warm_providers"].depends_on == ("load_session",)
