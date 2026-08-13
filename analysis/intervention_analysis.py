"""
Intervention Analysis
=====================

Moduł analizujący możliwe interwencje na podstawie:

- ryzyka,
- anomalii,
- patologii,
- trendu longitudinalnego,
- confidence,
- jakości danych.

Ten moduł NIE wykonuje interwencji.

Jego zadaniem jest przygotowanie kandydatów dla:

    decision/decision_engine.py

oraz:

    decision/intervention_rules.py
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Mapping, Optional


@dataclass
class InterventionCandidate:
    """
    Kandydat na potencjalną interwencję.
    """

    name: str
    priority: str
    rationale: str
    evidence_score: float
    confidence: float
    requires_review: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InterventionAnalyzer:
    """
    Analizator potencjalnych interwencji.

    Zwraca kandydatów, nie decyzje kliniczne.
    """

    def __init__(
        self,
        risk_threshold: float = 0.70,
        anomaly_threshold: float = 0.65,
        confidence_threshold: float = 0.60,
    ):
        self.risk_threshold = risk_threshold
        self.anomaly_threshold = anomaly_threshold
        self.confidence_threshold = confidence_threshold

    @staticmethod
    def _clip(value: float) -> float:
        return max(
            0.0,
            min(
                1.0,
                float(value),
            ),
        )

    def analyze(
        self,
        risk_score: float,
        anomaly_score: float,
        confidence: float,
        longitudinal_trend: Optional[float] = None,
        pathology_score: Optional[float] = None,
    ) -> List[InterventionCandidate]:
        """
        Tworzy listę kandydatów.

        longitudinal_trend:
            dodatnia wartość -> pogorszenie / wzrost ryzyka

        pathology_score:
            0-1.
        """

        risk_score = self._clip(
            risk_score
        )

        anomaly_score = self._clip(
            anomaly_score
        )

        confidence = self._clip(
            confidence
        )

        if longitudinal_trend is not None:
            longitudinal_trend = self._clip(
                longitudinal_trend
            )

        if pathology_score is not None:
            pathology_score = self._clip(
                pathology_score
            )

        candidates: List[
            InterventionCandidate
        ] = []

        # -------------------------------------------------
        # 1. Monitoring
        # -------------------------------------------------

        if risk_score >= 0.40:

            evidence = risk_score

            candidates.append(
                InterventionCandidate(
                    name="enhanced_monitoring",
                    priority=(
                        "high"
                        if risk_score >= 0.70
                        else "moderate"
                    ),
                    rationale=(
                        "Elevated global risk score "
                        "suggests increased monitoring."
                    ),
                    evidence_score=evidence,
                    confidence=confidence,
                    requires_review=(
                        confidence
                        < self.confidence_threshold
                    ),
                )
            )

        # -------------------------------------------------
        # 2. Further assessment
        # -------------------------------------------------

        if anomaly_score >= self.anomaly_threshold:

            evidence = anomaly_score

            candidates.append(
                InterventionCandidate(
                    name="additional_assessment",
                    priority=(
                        "high"
                        if anomaly_score >= 0.80
                        else "moderate"
                    ),
                    rationale=(
                        "Anomaly score is elevated "
                        "and may justify additional "
                        "assessment."
                    ),
                    evidence_score=evidence,
                    confidence=confidence,
                    requires_review=(
                        confidence
                        < self.confidence_threshold
                    ),
                )
            )

        # -------------------------------------------------
        # 3. Longitudinal reassessment
        # -------------------------------------------------

        if (
            longitudinal_trend is not None
            and longitudinal_trend >= 0.60
        ):

            candidates.append(
                InterventionCandidate(
                    name="longitudinal_reassessment",
                    priority="high",
                    rationale=(
                        "Longitudinal analysis indicates "
                        "a potentially meaningful change."
                    ),
                    evidence_score=longitudinal_trend,
                    confidence=confidence,
                    requires_review=True,
                )
            )

        # -------------------------------------------------
        # 4. Pathology review
        # -------------------------------------------------

        if (
            pathology_score is not None
            and pathology_score >= 0.70
        ):

            candidates.append(
                InterventionCandidate(
                    name="pathology_review",
                    priority="high",
                    rationale=(
                        "Pathology-related score is elevated "
                        "and should be reviewed."
                    ),
                    evidence_score=pathology_score,
                    confidence=confidence,
                    requires_review=True,
                )
            )

        # -------------------------------------------------
        # 5. Data review
        # -------------------------------------------------

        if confidence < self.confidence_threshold:

            candidates.append(
                InterventionCandidate(
                    name="data_quality_review",
                    priority="high",
                    rationale=(
                        "Model confidence is below the "
                        "configured threshold."
                    ),
                    evidence_score=(
                        1.0 - confidence
                    ),
                    confidence=confidence,
                    requires_review=True,
                )
            )

        return candidates

    def rank(
        self,
        candidates: List[
            InterventionCandidate
        ],
    ) -> List[
        InterventionCandidate
    ]:
        """
        Sortuje kandydatów według evidence score.
        """

        return sorted(
            candidates,
            key=lambda x: x.evidence_score,
            reverse=True,
        )

    def summarize(
        self,
        candidates: List[
            InterventionCandidate
        ],
    ) -> Dict[str, Any]:
        """
        Tworzy podsumowanie dla decision engine.
        """

        ranked = self.rank(
            candidates
        )

        return {
            "number_of_candidates": len(
                ranked
            ),
            "requires_review": any(
                c.requires_review
                for c in ranked
            ),
            "highest_priority": (
                ranked[0].name
                if ranked
                else None
            ),
            "candidates": [
                c.to_dict()
                for c in ranked
            ],
        }


def analyze_interventions(
    risk_score: float,
    anomaly_score: float,
    confidence: float,
) -> Dict[str, Any]:
    """
    Proste API modułu.
    """

    analyzer = InterventionAnalyzer()

    candidates = analyzer.analyze(
        risk_score=risk_score,
        anomaly_score=anomaly_score,
        confidence=confidence,
    )

    return analyzer.summarize(
        candidates
    )


if __name__ == "__main__":

    analyzer = InterventionAnalyzer()

    candidates = analyzer.analyze(
        risk_score=0.74,
        anomaly_score=0.69,
        confidence=0.81,
        longitudinal_trend=0.66,
        pathology_score=0.52,
    )

    summary = analyzer.summarize(
        candidates
    )

    print("Intervention analysis:")

    for candidate in summary[
        "candidates"
    ]:
        print(
            f"- {candidate['name']}: "
            f"{candidate['priority']} "
            f"(evidence="
            f"{candidate['evidence_score']:.3f})"
        )

    print("\nSummary:")
    print(summary)