"""
Aging Analysis
==============

Research-oriented analysis of biological-aging-related features.

This module does NOT diagnose biological age by itself.

It combines measurable features from:
- tissue
- cells
- morphology
- RNA
- optional hand/phenotypic data

into normalized aging-related feature summaries.

A learned aging model can later consume these features.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Mapping, Optional

import numpy as np


@dataclass
class AgingAnalysisResult:
    cellular_component: float
    tissue_component: float
    molecular_component: float
    morphology_component: float

    aging_feature_score: float

    feature_count: int

    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgingAnalyzer:
    """
    Compute a research-oriented aging feature profile.

    The default weights are intentionally simple and should be
    calibrated using real training data before scientific use.
    """

    def __init__(
        self,
        cellular_weight: float = 0.25,
        tissue_weight: float = 0.25,
        molecular_weight: float = 0.25,
        morphology_weight: float = 0.25,
    ):

        weights = np.asarray(
            [
                cellular_weight,
                tissue_weight,
                molecular_weight,
                morphology_weight,
            ],
            dtype=np.float32,
        )

        if np.any(weights < 0):
            raise ValueError(
                "Weights cannot be negative."
            )

        if np.sum(weights) == 0:
            raise ValueError(
                "At least one weight must be > 0."
            )

        self.weights = (
            weights
            / np.sum(weights)
        )

    # ------------------------------------------------------------------
    # Utility normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_value(
        value: Any,
    ) -> Optional[float]:

        if value is None:
            return None

        try:
            value = float(value)
        except (TypeError, ValueError):
            return None

        if not np.isfinite(value):
            return None

        return value

    @staticmethod
    def _normalize(
        value: float,
        low: float,
        high: float,
    ) -> float:

        if high <= low:
            return 0.0

        score = (
            (value - low)
            / (high - low)
        )

        return float(
            np.clip(score, 0.0, 1.0)
        )

    # ------------------------------------------------------------------
    # Cellular component
    # ------------------------------------------------------------------

    def cellular_score(
        self,
        cell_features: Mapping[str, Any],
    ) -> Optional[float]:

        values = []

        if "cell_distribution_score" in cell_features:
            value = self._safe_value(
                cell_features[
                    "cell_distribution_score"
                ]
            )

            if value is not None:
                values.append(
                    self._normalize(
                        value,
                        0.0,
                        2.0,
                    )
                )

        if "cell_density" in cell_features:
            value = self._safe_value(
                cell_features[
                    "cell_density"
                ]
            )

            if value is not None:
                values.append(
                    self._normalize(
                        value,
                        0.0,
                        0.01,
                    )
                )

        if not values:
            return None

        return float(
            np.mean(values)
        )

    # ------------------------------------------------------------------
    # Tissue component
    # ------------------------------------------------------------------

    def tissue_score(
        self,
        tissue_features: Mapping[str, Any],
    ) -> Optional[float]:

        values = []

        for key, low, high in [
            (
                "heterogeneity_score",
                0.0,
                1.0,
            ),
            (
                "spatial_complexity_score",
                0.0,
                1.0,
            ),
        ]:

            if key not in tissue_features:
                continue

            value = self._safe_value(
                tissue_features[key]
            )

            if value is not None:
                values.append(
                    self._normalize(
                        value,
                        low,
                        high,
                    )
                )

        if not values:
            return None

        return float(
            np.mean(values)
        )

    # ------------------------------------------------------------------
    # Molecular component
    # ------------------------------------------------------------------

    def molecular_score(
        self,
        rna_features: Mapping[str, Any],
    ) -> Optional[float]:

        values = []

        if "expression_std" in rna_features:

            value = self._safe_value(
                rna_features[
                    "expression_std"
                ]
            )

            if value is not None:
                values.append(
                    self._normalize(
                        value,
                        0.0,
                        5.0,
                    )
                )

        if "detected_genes_mean" in rna_features:

            value = self._safe_value(
                rna_features[
                    "detected_genes_mean"
                ]
            )

            if value is not None:
                values.append(
                    self._normalize(
                        value,
                        0.0,
                        5000.0,
                    )
                )

        if not values:
            return None

        return float(
            np.mean(values)
        )

    # ------------------------------------------------------------------
    # Morphology component
    # ------------------------------------------------------------------

    def morphology_score(
        self,
        morphology_features: Mapping[str, Any],
    ) -> Optional[float]:

        if (
            "morphology_abnormality_score"
            in morphology_features
        ):

            value = self._safe_value(
                morphology_features[
                    "morphology_abnormality_score"
                ]
            )

            if value is not None:
                return float(
                    np.clip(
                        value,
                        0.0,
                        1.0,
                    )
                )

        return None

    # ------------------------------------------------------------------
    # Complete analysis
    # ------------------------------------------------------------------

    def analyze(
        self,
        *,
        cell_features: Optional[
            Mapping[str, Any]
        ] = None,
        tissue_features: Optional[
            Mapping[str, Any]
        ] = None,
        rna_features: Optional[
            Mapping[str, Any]
        ] = None,
        morphology_features: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> AgingAnalysisResult:

        components = [
            (
                self.cellular_score(
                    cell_features or {}
                ),
                self.weights[0],
            ),
            (
                self.tissue_score(
                    tissue_features or {}
                ),
                self.weights[1],
            ),
            (
                self.molecular_score(
                    rna_features or {}
                ),
                self.weights[2],
            ),
            (
                self.morphology_score(
                    morphology_features or {}
                ),
                self.weights[3],
            ),
        ]

        valid_components = [
            (value, weight)
            for value, weight in components
            if value is not None
        ]

        if not valid_components:

            return AgingAnalysisResult(
                cellular_component=0.0,
                tissue_component=0.0,
                molecular_component=0.0,
                morphology_component=0.0,
                aging_feature_score=0.0,
                feature_count=0,
                confidence=0.0,
            )

        weighted_sum = sum(
            value * weight
            for value, weight
            in valid_components
        )

        total_weight = sum(
            weight
            for _, weight
            in valid_components
        )

        aging_score = (
            weighted_sum
            / (total_weight + 1e-8)
        )

        cellular = (
            components[0][0]
            if components[0][0] is not None
            else 0.0
        )

        tissue = (
            components[1][0]
            if components[1][0] is not None
            else 0.0
        )

        molecular = (
            components[2][0]
            if components[2][0] is not None
            else 0.0
        )

        morphology = (
            components[3][0]
            if components[3][0] is not None
            else 0.0
        )

        confidence = (
            total_weight
            / np.sum(self.weights)
        )

        return AgingAnalysisResult(
            cellular_component=float(
                cellular
            ),
            tissue_component=float(
                tissue
            ),
            molecular_component=float(
                molecular
            ),
            morphology_component=float(
                morphology
            ),
            aging_feature_score=float(
                np.clip(
                    aging_score,
                    0.0,
                    1.0,
                )
            ),
            feature_count=len(
                valid_components
            ),
            confidence=float(
                np.clip(
                    confidence,
                    0.0,
                    1.0,
                )
            ),
        )


def analyze_aging(
    *,
    cell_features: Optional[
        Mapping[str, Any]
    ] = None,
    tissue_features: Optional[
        Mapping[str, Any]
    ] = None,
    rna_features: Optional[
        Mapping[str, Any]
    ] = None,
    morphology_features: Optional[
        Mapping[str, Any]
    ] = None,
) -> Dict[str, Any]:

    analyzer = AgingAnalyzer()

    return analyzer.analyze(
        cell_features=cell_features,
        tissue_features=tissue_features,
        rna_features=rna_features,
        morphology_features=morphology_features,
    ).to_dict()


if __name__ == "__main__":

    print("Aging Analysis")

    cell_features = {
        "cell_density": 0.004,
        "cell_distribution_score": 0.8,
    }

    tissue_features = {
        "heterogeneity_score": 0.35,
        "spatial_complexity_score": 0.25,
    }

    rna_features = {
        "expression_std": 1.5,
        "detected_genes_mean": 1800,
    }

    morphology_features = {
        "morphology_abnormality_score": 0.30,
    }

    analyzer = AgingAnalyzer()

    result = analyzer.analyze(
        cell_features=cell_features,
        tissue_features=tissue_features,
        rna_features=rna_features,
        morphology_features=morphology_features,
    )

    print(
        f"Cellular component: "
        f"{result.cellular_component:.4f}"
    )

    print(
        f"Tissue component: "
        f"{result.tissue_component:.4f}"
    )

    print(
        f"Molecular component: "
        f"{result.molecular_component:.4f}"
    )

    print(
        f"Morphology component: "
        f"{result.morphology_component:.4f}"
    )

    print(
        f"Aging feature score: "
        f"{result.aging_feature_score:.4f}"
    )

    print(
        f"Feature count: "
        f"{result.feature_count}"
    )

    print(
        f"Confidence: "
        f"{result.confidence:.4f}"
    )

    print(
        "\nAging analysis ready."
    )