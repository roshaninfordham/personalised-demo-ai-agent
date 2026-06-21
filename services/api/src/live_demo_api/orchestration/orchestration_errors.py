"""Orchestration-specific errors."""

from __future__ import annotations


class OrchestrationError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class OrchestrationLockError(OrchestrationError):
    pass


class OrchestrationStateError(OrchestrationError):
    pass


class OrchestrationClientError(OrchestrationError):
    pass
