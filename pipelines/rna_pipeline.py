"""RNA analysis pipeline that converts transcriptomic features into core observations."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from analysis.rna_analysis import RNAAnalyzer
from core import (
    AnatomicalLocation,
    Biomarker,
    BiologicalState,
    Measurement,
    Observation,
    Person,
    Timepoint,
    Uncertainty,
)


class RNAPipeline:
    """Run RNA analysis and publish summary features to BiologicalState."""

    def __init__(self, analyzer: RNAAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RNAAnalyzer()

    def run(
        self,
        expression: np.ndarray,
        person: Person,
        timepoint: Timepoint,
        location: AnatomicalLocation,
        quality_score: float = 1.0,
        source: str = "rna_pipeline",
    ) -> BiologicalState:
        result = self.analyzer.analyze(expression)
        state = BiologicalState(
            subject_id=person.id,
            timepoint_id=timepoint.id,
            metadata={"pipeline": "rna", "source": source},
        )

        features = {
            "rna_cell_count": (float(result.n_cells), "count"),
            "rna_gene_count": (float(result.n_genes), "count"),
            "rna_mean_expression": (result.mean_expression, None),
            "rna_expression_std": (result.expression_std, None),
            "rna_mean_library_size": (result.mean_library_size, None),
            "rna_median_library_size": (result.median_library_size, None),
            "rna_mean_detected_genes": (result.detected_genes_mean, "count"),
            "rna_pca_dimension": (
                float(result.pca_shape[1]) if result.pca_shape else 0.0,
                "components",
            ),
        }

        uncertainty = Uncertainty(
            confidence=quality_score,
            quality_score=quality_score,
        )

        for name, (value, unit) in features.items():
            biomarker = Biomarker(
                id=name,
                name=name.replace("_", " "),
                category="transcriptomics",
                unit=unit,
            )
            measurement = Measurement(
                subject_id=person.id,
                timepoint_id=timepoint.id,
                modality="RNA",
                biomarker_id=biomarker.id,
                value=value,
                anatomical_location_id=location.id,
                source=source,
                uncertainty=uncertainty,
            )
            observation = Observation.from_measurement(measurement)
            state.add_observation(observation)

        state.set_dimension(
            "rna_expression_activity",
            result.mean_expression,
        )
        state.set_dimension(
            "rna_gene_detection",
            result.detected_genes_mean,
        )

        return state
