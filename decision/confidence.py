# decision/confidence.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ConfidenceResult:
    """
    Wynik oceny wiarygodności predykcji/decyzji.
    """

    score: float
    level: str
    components: Dict[str, float]
    explanation: str


class ConfidenceEstimator:
    """
    Agreguje różne źródła niepewności.

    Confidence nie jest prawdopodobieństwem medycznym.
    Jest wewnętrzną miarą jakości/pewności systemu.
    """

    def __init__(
        self,
        model_weight: float = 0.40,
        data_weight: float = 0.20,
        temporal_weight: float = 0.15,
        consistency_weight: float = 0.15,
        completeness_weight: float = 0.10,
    ):
        weights = {
            "model": model_weight,
            "data": data_weight,
            "temporal": temporal_weight,
            "consistency": consistency_weight,
            "completeness": completeness_weight,
        }

        total = sum(weights.values())

        if total <= 0:
            raise ValueError("Sum of confidence weights must be > 0.")

        self.weights = {
            key: value / total
            for key, value in weights.items()
        }

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def calculate(
        self,
        model_confidence: float,
        data_quality: float = 1.0,
        temporal_consistency: float = 1.0,
        multimodal_consistency: float = 1.0,
        data_completeness: float = 1.0,
    ) -> ConfidenceResult:

        components = {
            "model": self._clip(model_confidence),
            "data": self._clip(data_quality),
            "temporal": self._clip(temporal_consistency),
            "consistency": self._clip(multimodal_consistency),
            "completeness": self._clip(data_completeness),
        }

        score = sum(
            components[key] * self.weights[key]
            for key in components
        )

        if score >= 0.85:
            level = "high"
        elif score >= 0.65:
            level = "moderate"
        elif score >= 0.40:
            level = "low"
        else:
            level = "very_low"

        explanation = (
            f"Overall confidence={score:.3f}; "
            f"level={level}."
        )

        return ConfidenceResult(
            score=float(score),
            level=level,
            components=components,
            explanation=explanation,
        )


def confidence_from_probability(
    probability: float,
    distance_from_uncertainty: bool = True,
) -> float:
    """
    Zamienia prawdopodobieństwo klasy na prostą miarę confidence.

    Dla klasyfikacji binarnej:
        p=0.5 -> confidence=0
        p=0.9 -> confidence=0.8
        p=0.99 -> confidence=0.98
    """

    p = max(0.0, min(1.0, float(probability)))

    if distance_from_uncertainty:
        return min(1.0, 2.0 * abs(p - 0.5))

    return p


def confidence_from_margin(
    margin: float,
) -> float:
    """
    Confidence na podstawie marginesu między klasami.

    Przykład:
        margin=0.0 -> 0
        margin=0.5 -> 0.5
        margin=1.0 -> 1
    """

    return max(0.0, min(1.0, abs(float(margin))))


if __name__ == "__main__":
    estimator = ConfidenceEstimator()

    result = estimator.calculate(
        model_confidence=0.91,
        data_quality=0.88,
        temporal_consistency=0.80,
        multimodal_consistency=0.92,
        data_completeness=0.95,
    )

    print("Confidence result:")
    print(result)