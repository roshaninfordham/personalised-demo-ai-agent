"""Lead summary validation."""

from __future__ import annotations

from typing import Any


class SummaryValidator:
    def validate(self, summary: dict[str, Any]) -> bool:
        qualification = summary.get("qualification")
        if not isinstance(qualification, dict):
            return False
        score = qualification.get("overall_score", 0)
        confidence = qualification.get("confidence", 0)
        if not isinstance(score, int) or score < 0 or score > 100:
            return False
        if not isinstance(confidence, int | float) or confidence < 0 or confidence > 1:
            return False
        evidence = summary.get("evidence_summary")
        return isinstance(evidence, dict)
