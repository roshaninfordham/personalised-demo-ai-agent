from live_demo_backend_common.observability import span_names
from live_demo_backend_common.observability.tracing import (
    clear_finished_spans,
    get_finished_spans,
    start_span,
)


def test_turn_process_contains_child_spans() -> None:
    clear_finished_spans()
    with start_span(span_names.TURN_PROCESS):
        with start_span(span_names.TURN_CONTEXT_BUILD):
            pass
        with start_span(span_names.TURN_LLM_REQUEST, attributes={"prompt": "secret prompt"}):
            pass
        with start_span(span_names.VOICE_TTS_FIRST_AUDIO):
            pass
        with start_span(span_names.TURN_TOOL_ROUTE):
            pass

    spans = get_finished_spans()
    names = {span.name for span in spans}

    assert span_names.TURN_PROCESS in names
    assert span_names.TURN_CONTEXT_BUILD in names
    assert span_names.TURN_LLM_REQUEST in names
    assert span_names.VOICE_TTS_FIRST_AUDIO in names
    assert span_names.TURN_TOOL_ROUTE in names
    assert all("secret prompt" not in str(span.attributes) for span in spans)


def test_error_span_marked_as_error() -> None:
    clear_finished_spans()
    try:
        with start_span(span_names.BROWSER_ACTION_EXECUTE):
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    assert get_finished_spans()[-1].status == "error"
