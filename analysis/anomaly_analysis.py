"""
Anomaly Analysis
================

Analiza anomalii biologicznych i morfologicznych.

Moduł:
- analizuje score anomalii,
- klasyfikuje poziom anomalii,
- identyfikuje najbardziej podejrzane cechy,
- agreguje wyniki z wielu modalności,
- przygotowuje wynik dla decision engine i digital twin.

Nie jest to moduł diagnostyczny.
Wyniki są wskaźnikami analitycznymi modelu.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence

import math
import numpy as np


@dataclass
class AnomalyResult:
    """
    Wynik analizy anomalii.
    """

    score: float
    level: str
    is_anomalous: bool
    confidence: float
    top_features: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnomalyAnalyzer:
    """
    Analizator wyników modelu abnormality/anomaly.

    Domyślna interpretacja:

        0.00 - 0.30 -> low
        0.30 - 0.60 -> moderate
        0.60 - 0.80 -> high
        0.80 - 1.00 -> very_high
    """

    def __init__(
        self,
        anomaly_threshold: float = 0.50,
        high_threshold: float = 0.70,
        very_high_threshold: float = 0.85,
    ):
        self.anomaly_threshold = float(anomaly_threshold)
        self.high_threshold = float(high_threshold)
        self.very_high_threshold = float(very_high_threshold)

    @staticmethod
    def _clip_score(score: float) -> float:
        return float(np.clip(score, 0.0, 1.0))

    def classify_score(self, score: float) -> str:
        """
        Klasyfikuje score anomalii.
        """

        score = self._clip_score(score)

        if score >= self.very_high_threshold:
            return "very_high"

        if score >= self.high_threshold:
            return "high"

        if score >= self.anomaly_threshold:
            return "moderate"

        return "low"

    def estimate_confidence(self, score: float) -> float:
        """
        Szacuje confidence na podstawie odległości od środka 0.5.

        Jest to prosty wskaźnik pomocniczy, a nie kalibracja
        probabilistyczna.
        """

        score = self._clip_score(score)

        confidence = abs(score - 0.5) * 2.0

        return float(np.clip(confidence, 0.0, 1.0))

    def analyze(
        self,
        score: float,
        feature_names: Optional[Sequence[str]] = None,
        feature_values: Optional[Sequence[float]] = None,
        top_k: int = 10,
    ) -> AnomalyResult:
        """
        Analizuje pojedynczy wynik anomalii.

        Parameters
        ----------
        score:
            Score anomalii 0-1.

        feature_names:
            Nazwy cech.

        feature_values:
            Wartości/ważności cech.

        top_k:
            Liczba najważniejszych cech.
        """

        score = self._clip_score(score)

        level = self.classify_score(score)

        is_anomalous = score >= self.anomaly_threshold

        confidence = self.estimate_confidence(score)

        top_features: List[Dict[str, Any]] = []

        if feature_names is not None and feature_values is not None:
            if len(feature_names) != len(feature_values):
                raise ValueError(
                    "feature_names and feature_values must have equal length."
                )

            pairs = list(zip(feature_names, feature_values))

            pairs.sort(
                key=lambda x: abs(float(x[1])),
                reverse=True,
            )

            for name, value in pairs[:top_k]:
                top_features.append(
                    {
                        "feature": str(name),
                        "value": float(value),
                        "absolute_importance": abs(float(value)),
                    }
                )

        return AnomalyResult(
            score=score,
            level=level,
            is_anomalous=is_anomalous,
            confidence=confidence,
            top_features=top_features,
        )

    def aggregate(
        self,
        scores: Sequence[float],
        weights: Optional[Sequence[float]] = None,
    ) -> Dict[str, Any]:
        """
        Agreguje wyniki anomalii z wielu źródeł.

        Przykład:

        image anomaly
        cell anomaly
        RNA anomaly
        morphology anomaly

        -> jeden globalny anomaly score.
        """

        if len(scores) == 0:
            raise ValueError("scores cannot be empty.")

        values = np.asarray(scores, dtype=float)
        values = np.clip(values, 0.0, 1.0)

        if weights is None:
            weights_array = np.ones_like(values)
        else:
            weights_array = np.asarray(weights, dtype=float)

            if len(weights_array) != len(values):
                raise ValueError(
                    "scores and weights must have equal length."
                )

            if np.any(weights_array < 0):
                raise ValueError("weights must be non-negative.")

        weight_sum = weights_array.sum()

        if weight_sum <= 0:
            raise ValueError("Sum of weights must be greater than zero.")

        weighted_score = float(
            np.sum(values * weights_array) / weight_sum
        )

        result = self.analyze(weighted_score)

        return {
            "global_score": result.score,
            "level": result.level,
            "is_anomalous": result.is_anomalous,
            "confidence": result.confidence,
            "component_scores": values.tolist(),
        }


def analyze_anomaly(
    score: float,
    threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Prosta funkcja API.
    """

    analyzer = AnomalyAnalyzer(
        anomaly_threshold=threshold
    )

    return analyzer.analyze(score).to_dict()


if __name__ == "__main__":

    analyzer = AnomalyAnalyzer()

    result = analyzer.analyze(
        score=0.72,
        feature_names=[
            "morphology",
            "texture",
            "cell_density",
            "nuclear_features",
        ],
        feature_values=[
            0.20,
            0.81,
            0.63,
            0.91,
        ],
    )

    print("Anomaly analysis:")
    print(result.to_dict())