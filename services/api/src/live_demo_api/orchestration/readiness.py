"""Readiness scoring for prewarmed demo sessions."""

from __future__ import annotations

from live_demo_api.config import ApiSettings, get_settings
from live_demo_api.orchestration.orchestration_types import ReadinessState


def compute_readiness(
    *,
    browser_session_ready: bool,
    url_loaded: bool,
    first_screen_read: bool,
    safe_action_count: int,
    voice_session_ready: bool,
    join_config_ready: bool,
    recipe_compiled: bool,
    learner_enqueued: bool,
    provider_warmed_count: int,
    provider_required_count: int = 3,
    degraded_reasons: tuple[str, ...] = (),
) -> ReadinessState:
    safe_actions_available = min(1.0, safe_action_count / 3)
    providers_warmed = (
        1.0
        if provider_required_count <= 0
        else min(1.0, provider_warmed_count / provider_required_count)
    )
    score = (
        0.20 * float(browser_session_ready)
        + 0.15 * float(url_loaded)
        + 0.15 * float(first_screen_read)
        + 0.10 * safe_actions_available
        + 0.15 * float(voice_session_ready)
        + 0.10 * float(join_config_ready)
        + 0.05 * float(recipe_compiled)
        + 0.05 * float(learner_enqueued)
        + 0.05 * providers_warmed
    )
    return ReadinessState(
        score=round(score, 4),
        browser_session_ready=browser_session_ready,
        url_loaded=url_loaded,
        first_screen_read=first_screen_read,
        safe_action_count=safe_action_count,
        voice_session_ready=voice_session_ready,
        join_config_ready=join_config_ready,
        recipe_compiled=recipe_compiled,
        learner_enqueued=learner_enqueued,
        provider_warmed_count=provider_warmed_count,
        provider_required_count=provider_required_count,
        degraded_reasons=tuple(sorted(dict.fromkeys(degraded_reasons))),
    )


def readiness_allows_start(
    readiness: ReadinessState,
    settings: ApiSettings | None = None,
) -> tuple[bool, str]:
    settings = settings or get_settings()
    if settings.prewarm_require_browser_ready and not (
        readiness.browser_session_ready and readiness.url_loaded and readiness.first_screen_read
    ):
        return False, "browser_required_not_ready"
    if settings.prewarm_require_voice_ready and not (
        readiness.voice_session_ready and readiness.join_config_ready
    ):
        return False, "voice_required_not_ready"
    if readiness.score >= settings.prewarm_min_readiness_score:
        return True, "ready"
    if settings.prewarm_allow_degraded_ready:
        return True, "degraded_ready"
    return False, "readiness_below_threshold"
