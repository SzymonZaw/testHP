# decision/intervention_rules.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class InterventionDecision:
    """
    Klasyfikacja sugerowanego następnego działania systemu.
    """

    category: str
    priority: str
    rationale: str
    score: float


class InterventionRules:
    """
    Reguły określające poziom i typ następnego działania.

    System nie powinien automatycznie traktować tych wyników
    jako diagnozy lub indywidualnej terapii.
    """

    def __init__(
        self,
        monitoring_threshold: float = 0.40,
        review_threshold: float = 0.65,
        urgent_review_threshold: float = 0.85,
    ):
        self.monitoring_threshold = monitoring_threshold
        self.review_threshold = review_threshold
        self.urgent_review_threshold = urgent_review_threshold

    def decide(
        self,
        risk_score: float,
        abnormality_score: float = 0.0,
        pathology_score: float = 0.0,
        confidence: float = 1.0,
    ) -> InterventionDecision:

        risk_score = float(risk_score)
        abnormality_score = float(abnormality_score)
        pathology_score = float(pathology_score)
        confidence = float(confidence)

        combined_score = max(
            risk_score,
            abnormality_score,
            pathology_score,
        )

        if confidence < 0.50:
            return InterventionDecision(
                category="insufficient_confidence",
                priority="low",
                rationale=(
                    "Prediction confidence is insufficient "
                    "for a stronger automated decision."
                ),
                score=confidence,
            )

        if combined_score >= self.urgent_review_threshold:
            return InterventionDecision(
                category="urgent_review",
                priority="high",
                rationale=(
                    "High model-derived risk/abnormality signal "
                    "requires additional review."
                ),
                score=combined_score,
            )

        if combined_score >= self.review_threshold:
            return InterventionDecision(
                category="additional_review",
                priority="medium",
                rationale=(
                    "Model outputs indicate that additional "
                    "analysis or review may be appropriate."
                ),
                score=combined_score,
            )

        if combined_score >= self.monitoring_threshold:
            return InterventionDecision(
                category="monitoring",
                priority="low",
                rationale=(
                    "Moderate signal detected; longitudinal "
                    "monitoring may be useful."
                ),
                score=combined_score,
            )

        return InterventionDecision(
            category="no_intervention_signal",
            priority="low",
            rationale=(
                "No strong intervention-related signal "
                "was detected by the current models."
            ),
            score=combined_score,
        )


if __name__ == "__main__":
    rules = InterventionRules()

    decision = rules.decide(
        risk_score=0.72,
        abnormality_score=0.60,
        pathology_score=0.55,
        confidence=0.88,
    )

    print(decision)