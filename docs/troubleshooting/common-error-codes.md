# Common Error Codes

| Error code | Component | Meaning | Likely fix |
| --- | --- | --- | --- |
| `browser_runtime_unavailable` | browser/API | Browser runtime cannot be reached | Check `browser-runtime` health and logs |
| `navigation_blocked` | browser policy | Target URL was blocked | Check allowed domains and local URL settings |
| `screen_read_timeout` | browser | Screen read exceeded timeout | Check target app, memory, and timeout settings |
| `policy_blocked` | safety | Action failed policy | Use a safer action or adjust recipe constraints |
| `provider_authentication_error` | provider | Provider key invalid or missing | Verify backend env key |
| `provider_rate_limited` | provider | Provider returned rate limit | Wait, reduce load, or switch provider |
| `invalid_agent_output` | agent | LLM output failed schema/policy validation | Use a validated model or fake provider |
| `voice_session_not_connected` | agent/transport | User did not connect to voice session | Check join config and transport |
| `tts_unavailable` | agent/TTS | TTS provider failed | Switch to fake TTS or fix provider |
| `stt_unavailable` | agent/STT | STT provider failed | Switch to fake STT or fix provider |
| `recipe_validation_failed` | recipe | Recipe failed schema or safety validation | Fix recipe JSON |
| `prewarm_failed` | orchestrator | Required prewarm task failed | Check browser, voice, and DB/Redis |
| `recovery_failed` | orchestrator/browser | Recovery attempts exhausted | End session or switch to safe fallback |
