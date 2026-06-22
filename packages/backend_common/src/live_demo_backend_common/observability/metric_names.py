"""Canonical metric names and low-cardinality label allowlist."""

SESSION_STARTED_TOTAL = "live_demo_sessions_started_total"
SESSION_COMPLETED_TOTAL = "live_demo_sessions_completed_total"
SESSIONS_ACTIVE_CURRENT = "live_demo_sessions_active_current"
SESSION_DURATION_SECONDS = "live_demo_session_duration_seconds"
FIRST_AUDIO_LATENCY_SECONDS = "live_demo_first_audio_latency_seconds"
TURN_LATENCY_SECONDS = "live_demo_turn_latency_seconds"
USER_INTERRUPTIONS_TOTAL = "live_demo_user_interruptions_total"
INTERRUPTION_STOP_LATENCY_SECONDS = "live_demo_interruption_stop_latency_seconds"
STT_LATENCY_SECONDS = "live_demo_stt_latency_seconds"
TTS_FIRST_AUDIO_LATENCY_SECONDS = "live_demo_tts_first_audio_latency_seconds"
LLM_LATENCY_SECONDS = "live_demo_llm_latency_seconds"
LLM_FIRST_TOKEN_LATENCY_SECONDS = "live_demo_llm_first_token_latency_seconds"  # noqa: S105
LLM_TOKENS_TOTAL = "live_demo_llm_tokens_total"
MODEL_INVOCATIONS_TOTAL = "live_demo_model_invocations_total"
BROWSER_ACTIONS_TOTAL = "live_demo_browser_actions_total"
BROWSER_ACTION_LATENCY_SECONDS = "live_demo_browser_action_latency_seconds"
BROWSER_SCREEN_READ_LATENCY_SECONDS = "live_demo_browser_screen_read_latency_seconds"
BROWSER_SCREENSHOT_CAPTURE_LATENCY_SECONDS = "live_demo_browser_screenshot_capture_latency_seconds"
BROWSER_SESSIONS_ACTIVE_CURRENT = "live_demo_browser_sessions_active_current"
POLICY_EVALUATIONS_TOTAL = "live_demo_policy_evaluations_total"
POLICY_BLOCKS_TOTAL = "live_demo_policy_blocks_total"
POLICY_EVALUATION_LATENCY_SECONDS = "live_demo_policy_evaluation_latency_seconds"
LEARNER_JOBS_TOTAL = "live_demo_learner_jobs_total"
LEARNER_JOB_DURATION_SECONDS = "live_demo_learner_job_duration_seconds"
KNOWLEDGE_CHUNKS_TOTAL = "live_demo_knowledge_chunks_total"
KNOWLEDGE_RETRIEVAL_LATENCY_SECONDS = "live_demo_knowledge_retrieval_latency_seconds"
POST_DEMO_JOBS_TOTAL = "live_demo_post_demo_jobs_total"
POST_DEMO_JOB_DURATION_SECONDS = "live_demo_post_demo_job_duration_seconds"
CRM_EXPORTS_TOTAL = "live_demo_crm_exports_total"
LEAD_SUMMARIES_GENERATED_TOTAL = "live_demo_lead_summaries_generated_total"
EVENTS_PUBLISHED_TOTAL = "live_demo_events_published_total"
EVENT_PUBLISH_LATENCY_SECONDS = "live_demo_event_publish_latency_seconds"
EVENT_LAG_SECONDS = "live_demo_event_lag_seconds"
REDIS_OPERATION_LATENCY_SECONDS = "live_demo_redis_operation_latency_seconds"
ERRORS_TOTAL = "live_demo_errors_total"
AGENT_OUTPUT_VALIDATION_FAILURES_TOTAL = "live_demo_agent_output_validation_failures_total"
AGENT_FALLBACK_DECISIONS_TOTAL = "live_demo_agent_fallback_decisions_total"
MEMORY_UPDATES_TOTAL = "live_demo_memory_updates_total"
RECIPE_STEPS_COMPLETED_TOTAL = "live_demo_recipe_steps_completed_total"
RECIPE_STEPS_FAILED_TOTAL = "live_demo_recipe_steps_failed_total"
WORKER_QUEUE_DEPTH_CURRENT = "live_demo_worker_queue_depth_current"
ESTIMATED_COST_USD_TOTAL = "live_demo_estimated_cost_usd_total"
TTS_AUDIO_SECONDS_TOTAL = "live_demo_tts_audio_seconds_total"
STT_AUDIO_SECONDS_TOTAL = "live_demo_stt_audio_seconds_total"
EMBEDDING_VECTORS_TOTAL = "live_demo_embedding_vectors_total"
LATENCY_BUDGET_CHECKS_TOTAL = "live_demo_latency_budget_checks_total"
LATENCY_BUDGET_VIOLATIONS_TOTAL = "live_demo_latency_budget_violations_total"
LATENCY_BUDGET_EXCESS_SECONDS = "live_demo_latency_budget_excess_seconds"

ALL_METRIC_NAMES = frozenset(
    value
    for key, value in globals().items()
    if key.isupper() and isinstance(value, str) and value.startswith("live_demo_")
)

ALLOWED_LABEL_NAMES = frozenset(
    {
        "service",
        "environment",
        "operation",
        "status",
        "provider",
        "model_family",
        "purpose",
        "transport_provider",
        "action_type",
        "risk_level",
        "policy_decision",
        "policy_type",
        "decision",
        "reason_code",
        "phase",
        "error_code",
        "route",
        "method",
        "trigger",
        "result",
        "job_type",
        "source_type",
        "retrieval_type",
        "event_type_group",
        "component",
        "severity",
        "dry_run",
        "mode",
        "token_type",
        "format",
    }
)
