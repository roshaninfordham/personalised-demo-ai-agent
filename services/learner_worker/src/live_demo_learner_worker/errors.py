"""Typed learner worker errors."""

from __future__ import annotations


class LearnerWorkerError(Exception):
    code = "learner_error"
    retryable = False

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class RetryableLearnerError(LearnerWorkerError):
    code = "retryable_learner_error"
    retryable = True


class NonRetryableLearnerError(LearnerWorkerError):
    code = "non_retryable_learner_error"
    retryable = False


class LearnerJobValidationError(NonRetryableLearnerError):
    code = "invalid_learner_job"


class LearnerSafetyError(NonRetryableLearnerError):
    code = "learner_safety_blocked"


class LearnerTimeoutError(RetryableLearnerError):
    code = "learner_timeout"
