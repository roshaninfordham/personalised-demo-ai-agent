from __future__ import annotations

from live_demo_backend_common.policy.redaction import RedactionEngine
from live_demo_learner_worker.redaction.learner_redaction import LearnerRedactor


def test_learner_redaction_masks_email() -> None:
    result = LearnerRedactor(RedactionEngine()).redact_for_embedding("Contact alice@example.com")

    assert result.applied
    assert "[REDACTED_EMAIL]" in str(result.redacted_value)
