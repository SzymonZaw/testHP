"""Convert tissue imaging features into core observations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import numpy as np

from analysis.tissue_analysis import TissueAnalyzer
from core import AnatomicalLocation, Biomarker, BiologicalState, Measurement, Observation, Person, Timepoint, Uncertainty


class TissuePipeline:
    """Run tissue analysis and publish summary features to BiologicalState."""

    def __init__(self, analyzer: TissueAnalyzer | None = None) -> None:
        self.analyzer = analyzer or TissueAnalyzer()

    def run(self, image: np.ndarray, person: Person, timepoint: Timepoint,
            location: AnatomicalLocation, mask: np.ndarray | None = None,
            quality_score: float = 1.0, source: str = "tissue_pipeline") -> BiologicalState:
        result = self.analyzer.analyze(image=image, mask=mask)
        state = BiologicalState(subject_id=person.id, timepoint_id=timepoint.id,
                                metadata={"pipeline": "tissue", "source": source})
        features = {
            "tissue_area": (result.tissue_area, "pixel"),
            "tissue_occupied_area": (result.occupied_area, "pixel"),
            "tissue_occupancy_ratio": (result.occupancy_ratio, None),
            "tissue_mean_intensity": (result.mean_intensity, None),
            "tissue_intensity_std": (result.std_intensity, None),
            "tissue_region_count": (float(result.region_count), "count"),
            "tissue_mean_region_area": (result.mean_region_area, "pixel"),
            "tissue_largest_region_area": (result.largest_region_area, "pixel"),
            "tissue_heterogeneity": (result.heterogeneity_score, None),
            "tissue_spatial_complexity": (result.spatial_complexity_score, None),
        }
        uncertainty = Uncertainty(confidence=quality_score, quality_score=quality_score)
        now = datetime.now(timezone.utc)
        for name, (value, unit) in features.items():
            biomarker = Biomarker(id=name, name=name.replace("_", " "), category="tissue_morphology", unit=unit)
            measurement = Measurement(
                id=f"measurement-{uuid4().hex}", subject_id=person.id, timepoint_id=timepoint.id,
                modality="tissue_imaging", biomarker=biomarker, value=value, measured_at=now,
                anatomical_location=location, unit=unit, source=source, uncertainty=uncertainty,
            )
            observation = Observation(
                id=f"observation-{uuid4().hex}", subject_id=person.id, timepoint_id=timepoint.id,
                name=name, value=value, observed_at=now, anatomical_location=location,
                uncertainty=uncertainty, source_measurement_ids=[measurement.id],
                metadata={"modality": "tissue_imaging", "biomarker_id": biomarker.id},
            )
            state.add_observation(observation)
        state.set_dimension("tissue_occupancy", result.occupancy_ratio)
        state.set_dimension("tissue_heterogeneity", result.heterogeneity_score)
        state.set_dimension("tissue_spatial_complexity", result.spatial_complexity_score)
        return state
