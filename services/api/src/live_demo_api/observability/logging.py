"""Compatibility wrapper for shared structured logging."""

from live_demo_backend_common.observability.logging import (
    JsonLogFormatter,
    configure_json_logging,
    log_event,
)

__all__ = ["JsonLogFormatter", "configure_json_logging", "log_event"]
