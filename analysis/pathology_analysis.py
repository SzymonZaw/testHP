"""
Pathology Analysis
==================

Interpretacja wyników modelu patologicznego.

Moduł:
- interpretuje prawdopodobieństwa klas,
- wyznacza klasę dominującą,
- oblicza confidence,
- analizuje uncertainty,
- agreguje wyniki z wielu próbek/patchy,
- przygotowuje wynik dla kolejnych modułów.

Nie stanowi samodzielnego systemu diagnostycznego.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence

import numpy as np


@dataclass
class PathologyResult:
    """
    Wynik analizy patologicznej.
    """

    predicted_class: str
    confidence: float
    entropy: float
    probabilities: Dict[str, float]
    uncertain: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PathologyAnalyzer:
    """
    Analizator wyników klasyfikacji patologicznej.
    """

    def __init__(
        self,
        uncertainty_threshold: float = 0.60,
    ):
        self.uncertainty_threshold = float(
            uncertainty_threshold
        )

    @staticmethod
    def _normalize_probabilities(
        probabilities: Sequence[float],
    ) -> np.ndarray:
        probs = np.asarray(
            probabilities,
            dtype=float,
        )

        if probs.ndim != 1:
            raise ValueError(
                "probabilities must be a 1D sequence."
            )

        if len(probs) == 0:
            raise ValueError(
                "probabilities cannot be empty."
            )

        if np.any(probs < 0):
            raise ValueError(
                "probabilities cannot be negative."
            )

        total = probs.sum()

        if total <= 0:
            raise ValueError(
                "Probability sum must be greater than zero."
            )

        return probs / total

    @staticmethod
    def entropy(probabilities: np.ndarray) -> float:
        """
        Normalizowana entropia predykcji.

        0 -> bardzo pewna predykcja
        1 -> maksymalna niepewność
        """

        probs = probabilities[
            probabilities > 0
        ]

        entropy = -np.sum(
            probs * np.log(probs)
        )

        max_entropy = np.log(
            len(probabilities)
        )

        if max_entropy == 0:
            return 0.0

        return float(
            entropy / max_entropy
        )

    def analyze(
        self,
        probabilities: Sequence[float],
        class_names: Optional[Sequence[str]] = None,
    ) -> PathologyResult:
        """
        Analizuje prawdopodobieństwa klas.
        """

        probs = self._normalize_probabilities(
            probabilities
        )

        if class_names is None:
            class_names = [
                f"class_{i}"
                for i in range(len(probs))
            ]

        if len(class_names) != len(probs):
            raise ValueError(
                "class_names and probabilities "
                "must have equal length."
            )

        predicted_index = int(
            np.argmax(probs)
        )

        predicted_class = str(
            class_names[predicted_index]
        )

        confidence = float(
            probs[predicted_index]
        )

        entropy = self.entropy(probs)

        uncertain = (
            confidence < self.uncertainty_threshold
        )

        probability_dict = {
            str(name): float(prob)
            for name, prob in zip(
                class_names,
                probs,
            )
        }

        return PathologyResult(
            predicted_class=predicted_class,
            confidence=confidence,
            entropy=entropy,
            probabilities=probability_dict,
            uncertain=uncertain,
        )

    def aggregate_patches(
        self,
        patch_probabilities: Sequence[
            Sequence[float]
        ],
        class_names: Sequence[str],
    ) -> PathologyResult:
        """
        Agreguje predykcje z wielu patchy obrazu.

        Każdy patch ma osobny wektor prawdopodobieństw.

        Wynik:
            średnie prawdopodobieństwo klas.
        """

        matrix = np.asarray(
            patch_probabilities,
            dtype=float,
        )

        if matrix.ndim != 2:
            raise ValueError(
                "patch_probabilities must be a 2D array."
            )

        mean_probabilities = matrix.mean(
            axis=0
        )

        return self.analyze(
            mean_probabilities,
            class_names,
        )

    def uncertainty_report(
        self,
        result: PathologyResult,
    ) -> Dict[str, Any]:
        """
        Tworzy prosty raport niepewności.
        """

        return {
            "predicted_class": result.predicted_class,
            "confidence": result.confidence,
            "entropy": result.entropy,
            "uncertain": result.uncertain,
            "interpretation": (
                "high uncertainty"
                if result.uncertain
                else "relatively confident"
            ),
        }


def analyze_pathology(
    probabilities: Sequence[float],
    class_names: Sequence[str],
) -> Dict[str, Any]:
    """
    Proste API modułu.
    """

    analyzer = PathologyAnalyzer()

    return analyzer.analyze(
        probabilities,
        class_names,
    ).to_dict()


if __name__ == "__main__":

    analyzer = PathologyAnalyzer()

    result = analyzer.analyze(
        probabilities=[
            0.08,
            0.17,
            0.75,
        ],
        class_names=[
            "normal",
            "uncertain",
            "abnormal",
        ],
    )

    print("Pathology analysis:")
    print(result.to_dict())

    print("\nUncertainty:")
    print(
        analyzer.uncertainty_report(result)
    )