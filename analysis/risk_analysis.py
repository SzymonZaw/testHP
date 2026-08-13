"""
Risk Analysis
=============

Agregacja czynników ryzyka pochodzących z wielu modalności.

Przykładowe źródła:

- morphology
- pathology
- abnormality
- RNA
- clinical data
- longitudinal progression
- hand/physical phenotype

Moduł tworzy globalny risk score.

Nie jest to kliniczny kalkulator ryzyka.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Mapping, Optional

import numpy as np


@dataclass
class RiskResult:
    """
    Wynik analizy ryzyka.
    """

    risk_score: float
    risk_level: str
    confidence: float
    components: Dict[str, float]
    dominant_factor: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RiskAnalyzer:
    """
    Analizator globalnego ryzyka.
    """

    def __init__(
        self,
        thresholds: Optional[
            Mapping[str, float]
        ] = None,
    ):
        self.thresholds = thresholds or {
            "low": 0.30,
            "moderate": 0.60,
            "high": 0.80,
        }

    @staticmethod
    def _clip(value: float) -> float:
        return float(
            np.clip(value, 0.0, 1.0)
        )

    def classify(
        self,
        score: float,
    ) -> str:

        score = self._clip(score)

        if score >= self.thresholds["high"]:
            return "high"

        if score >= self.thresholds["moderate"]:
            return "moderate"

        if score >= self.thresholds["low"]:
            return "low"

        return "very_low"

    def calculate_confidence(
        self,
        components: Mapping[str, float],
    ) -> float:
        """
        Confidence bazuje na zgodności komponentów.

        Jeśli wszystkie komponenty wskazują podobny poziom,
        confidence rośnie.

        Jeśli są bardzo rozbieżne,
        confidence spada.
        """

        values = np.asarray(
            list(components.values()),
            dtype=float,
        )

        if len(values) == 0:
            return 0.0

        values = np.clip(
            values,
            0.0,
            1.0,
        )

        dispersion = float(
            np.std(values)
        )

        confidence = 1.0 - dispersion

        return float(
            np.clip(
                confidence,
                0.0,
                1.0,
            )
        )

    def analyze(
        self,
        components: Mapping[str, float],
        weights: Optional[
            Mapping[str, float]
        ] = None,
    ) -> RiskResult:
        """
        Agreguje komponenty ryzyka.
        """

        if not components:
            raise ValueError(
                "components cannot be empty."
            )

        normalized_components = {
            name: self._clip(value)
            for name, value in components.items()
        }

        if weights is None:
            weights = {
                name: 1.0
                for name in normalized_components
            }

        weighted_values = []
        weight_values = []

        for name, value in normalized_components.items():

            weight = float(
                weights.get(name, 1.0)
            )

            if weight < 0:
                raise ValueError(
                    "Weights cannot be negative."
                )

            weighted_values.append(
                value * weight
            )

            weight_values.append(weight)

        weight_sum = sum(weight_values)

        if weight_sum <= 0:
            raise ValueError(
                "Total weight must be greater than zero."
            )

        risk_score = float(
            sum(weighted_values)
            / weight_sum
        )

        risk_level = self.classify(
            risk_score
        )

        confidence = self.calculate_confidence(
            normalized_components
        )

        dominant_factor = max(
            normalized_components,
            key=normalized_components.get,
        )

        return RiskResult(
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=confidence,
            components=normalized_components,
            dominant_factor=dominant_factor,
        )

    def compare_modalities(
        self,
        components: Mapping[str, float],
    ) -> Dict[str, Any]:
        """
        Porównuje wkład poszczególnych modalności.
        """

        sorted_components = sorted(
            components.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return {
            "ranking": [
                {
                    "source": name,
                    "score": float(score),
                }
                for name, score in sorted_components
            ]
        }


def calculate_risk(
    components: Mapping[str, float],
) -> Dict[str, Any]:
    """
    Proste API.
    """

    analyzer = RiskAnalyzer()

    return analyzer.analyze(
        components
    ).to_dict()


if __name__ == "__main__":

    analyzer = RiskAnalyzer()

    components = {
        "morphology": 0.62,
        "pathology": 0.48,
        "abnormality": 0.71,
        "rna": 0.55,
        "longitudinal": 0.67,
    }

    result = analyzer.analyze(
        components,
        weights={
            "morphology": 1.0,
            "pathology": 1.5,
            "abnormality": 1.5,
            "rna": 1.0,
            "longitudinal": 1.2,
        },
    )

    print("Risk analysis:")
    print(result.to_dict())

    print("\nModalities:")
    print(
        analyzer.compare_modalities(
            components
        )
    )