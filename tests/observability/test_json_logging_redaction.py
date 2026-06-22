import json
import logging

from live_demo_backend_common.observability.logging import JsonLogFormatter


def test_json_log_contains_trace_and_redacts_secrets() -> None:
    formatter = JsonLogFormatter(service="api", environment="local")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="llm.request.completed",
        args=(),
        exc_info=None,
    )
    record.trace_id = "trace"
    record.authorization = "Bearer secret-token"
    record.prompt = "raw prompt should not appear"

    payload = json.loads(formatter.format(record))

    assert payload["service"] == "api"
    assert payload["event_type"] == "llm.request.completed"
    assert payload["trace_id"] == "trace"
    assert payload["metadata"]["authorization"] == "***REDACTED***"
    assert payload["metadata"]["prompt"] == "***REDACTED***"
