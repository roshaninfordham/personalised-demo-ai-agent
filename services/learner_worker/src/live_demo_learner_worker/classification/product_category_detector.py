"""Product category detector."""

from __future__ import annotations

from dataclasses import dataclass

from live_demo_learner_worker.browser.browser_runtime_client import SafeAction, UIElement
from live_demo_learner_worker.classification.category_scoring import (
    element_labels,
    score_categories,
)
from live_demo_learner_worker.classification.demo_angle_generator import generate_demo_angles
from live_demo_learner_worker.classification.persona_inference import infer_personas


@dataclass(frozen=True, slots=True)
class ProductCategoryDetection:
    category: str
    confidence: float
    matched_keywords: tuple[str, ...]
    use_cases: tuple[str, ...]
    target_personas: tuple[str, ...]
    demo_angles: tuple[str, ...]
    evidence: tuple[str, ...]


class ProductCategoryDetector:
    def __init__(self, min_confidence: float = 0.50) -> None:
        self._min_confidence = min_confidence

    def detect(
        self,
        *,
        screen_summary: str,
        visible_text: str | None,
        elements: tuple[UIElement, ...],
        product_name: str | None,
        guidance_text: str | None,
        safe_actions: tuple[SafeAction, ...],
    ) -> ProductCategoryDetection:
        labels = element_labels(elements)
        score = score_categories(
            screen_summary=screen_summary,
            visible_text=visible_text,
            element_labels=labels,
            product_name=product_name,
            guidance_text=guidance_text,
            safe_actions=safe_actions,
            min_confidence=self._min_confidence,
        )
        return ProductCategoryDetection(
            category=score.category,
            confidence=score.confidence,
            matched_keywords=score.matched_keywords,
            use_cases=_use_cases(score.category),
            target_personas=infer_personas(score.category),
            demo_angles=generate_demo_angles(score.category),
            evidence=score.matched_keywords,
        )


def _use_cases(category: str) -> tuple[str, ...]:
    if category == "analytics_dashboard":
        return ("track KPIs", "review reports", "monitor trends")
    if category == "crm_sales":
        return ("manage pipeline", "track leads", "review opportunities")
    if category == "operations_workflow":
        return ("coordinate work", "track process status")
    return ("understand product capabilities",)
