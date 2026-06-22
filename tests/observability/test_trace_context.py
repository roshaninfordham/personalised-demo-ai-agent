from live_demo_backend_common.observability.trace_context import TraceContext, extract_trace_context


def test_new_trace_created_when_none_exists() -> None:
    context = TraceContext.from_headers({})

    assert len(context.trace_id) == 32
    assert len(context.span_id) == 16
    assert context.traceparent.startswith("00-")


def test_traceparent_propagated_through_http_client() -> None:
    context = TraceContext.new()
    headers = context.inject_headers()

    assert headers["traceparent"] == context.traceparent
    assert headers["x-trace-id"] == context.trace_id
    assert TraceContext.from_headers(headers).trace_id == context.trace_id


def test_traceparent_propagated_through_redis_job_payload() -> None:
    context = TraceContext.new()
    payload = context.inject_carrier({"job_id": "job"})

    assert payload["traceparent"] == context.traceparent
    assert extract_trace_context(payload).trace_id == context.trace_id
