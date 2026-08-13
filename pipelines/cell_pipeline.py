"""First end-to-end cell analysis pipeline.

Flow:
    image -> segmentation -> CellAnalyzer -> Measurement -> Observation
          -> BiologicalState

The pipeline is deliberately small and deterministic. It provides the
integration contract that future Cellpose/StarDist or other validated
segmentation models can plug into.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

from analysis.cell_analysis import CellAnalyzer
from core.anatomy import AnatomicalLocation
from core.biological_state import BiologicalState
from core.biomarker import Biomarker
from core.measurement import Measurement
from core.observation import Observation
from core.uncertainty import Uncertainty
from segmentation.cell_segmentation import segment_binary_cells


@dataclass
class CellPipelineResult:
    """Complete output of one cell-analysis run."""

    mask: np.ndarray
    analysis: dict[str, Any]
    measurements: list[Measurement] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    state: Optional[BiologicalState] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis": self.analysis,
            "measurements": [measurement.__dict__ for measurement in self.measurements],
            "observations": [observation.__dict__ for observation in self.observations],
            "state": {
                "subject_id": self.state.subject_id,
                "timepoint_id": self.state.timepoint_id,
                "observation_count": len(self.state.observations),
                "dimensions": dict(self.state.dimensions),
            } if self.state else None,
        }


def _biomarkers() -> dict[str, Biomarker]:
    return {
        "cell_count": Biomarker(
            id="cell_count",
            name="Cell count",
            category="cell_population",
            unit="count",
        ),
        "cell_density": Biomarker(
            id="cell_density",
            name="Cell density",
            category="cell_population",
            unit="cells/pixel²",
        ),
        "mean_cell_area": Biomarker(
            id="mean_cell_area",
            name="Mean cell area",
            category="cell_morphology",
            unit="pixel²",
        ),
        "mean_cell_compactness": Biomarker(
            id="mean_cell_compactness",
            name="Mean cell compactness",
            category="cell_morphology",
        ),
        "mean_nearest_neighbor_distance": Biomarker(
            id="mean_nearest_neighbor_distance",
            name="Mean nearest-neighbour distance",
            category="cell_spatial",
            unit="pixel",
        ),
        "cell_distribution_score": Biomarker(
            id="cell_distribution_score",
            name="Cell distribution score",
            category="cell_spatial",
        ),
    }


def _measurement_and_observation(
    *,
    metric_name: str,
    value: float,
    subject_id: str,
    timepoint_id: str,
    anatomical_location: AnatomicalLocation,
    measured_at: datetime,
    source: str,
    quality: float,
    biomarker: Biomarker,
) -> tuple[Measurement, Observation]:
    measurement_id = f"{timepoint_id}:{metric_name}:measurement"
    observation_id = f"{timepoint_id}:{metric_name}:observation"
    uncertainty = Uncertainty(confidence=quality)

    measurement = Measurement(
        id=measurement_id,
        subject_id=subject_id,
        timepoint_id=timepoint_id,
        modality="cell_microscopy",
        biomarker=biomarker,
        value=value,
        measured_at=measured_at,
        anatomical_location=anatomical_location,
        unit=biomarker.unit,
        uncertainty=uncertainty,
        source=source,
        processing_version="cell-pipeline-v1",
    )

    observation = Observation(
        id=observation_id,
        subject_id=subject_id,
        timepoint_id=timepoint_id,
        name=metric_name,
        value=value,
        observed_at=measured_at,
        anatomical_location=anatomical_location,
        uncertainty=uncertainty,
        source_measurement_ids=[measurement_id],
        metadata={"pipeline": "cell", "quality": quality},
    )
    return measurement, observation


def run_cell_pipeline(
    image: np.ndarray,
    *,
    subject_id: str,
    timepoint_id: str,
    anatomical_location: AnatomicalLocation,
    measured_at: Optional[datetime] = None,
    threshold: Optional[float] = None,
    min_area: int = 10,
    input_is_mask: bool = False,
    quality: float = 0.8,
) -> CellPipelineResult:
    """Run segmentation, cell analysis and core-state integration.

    ``input_is_mask=True`` is useful when a validated external segmenter such
    as Cellpose has already produced an instance mask.
    """
    if not subject_id.strip() or not timepoint_id.strip():
        raise ValueError("subject_id and timepoint_id cannot be empty")
    if not 0.0 <= quality <= 1.0:
        raise ValueError("quality must be between 0 and 1")

    measured_at = measured_at or datetime.now(timezone.utc)
    mask = np.asarray(image) if input_is_mask else segment_binary_cells(
        image,
        threshold=threshold,
        min_area=min_area,
    )

    analyzer = CellAnalyzer()
    analysis = analyzer.analyze(mask).to_dict()
    biomarkers = _biomarkers()

    metrics = {
        "cell_count": float(analysis["cell_count"]),
        "cell_density": float(analysis["cell_density"]),
        "mean_cell_area": float(analysis["mean_area"]),
        "mean_cell_compactness": float(analysis["mean_compactness"]),
        "mean_nearest_neighbor_distance": float(
            analysis["mean_nearest_neighbor_distance"]
        ),
        "cell_distribution_score": float(analysis["cell_distribution_score"]),
    }

    measurements: list[Measurement] = []
    observations: list[Observation] = []
    state = BiologicalState(subject_id=subject_id, timepoint_id=timepoint_id)

    for metric_name, value in metrics.items():
        measurement, observation = _measurement_and_observation(
            metric_name=metric_name,
            value=value,
            subject_id=subject_id,
            timepoint_id=timepoint_id,
            anatomical_location=anatomical_location,
            measured_at=measured_at,
            source="cell_pipeline",
            quality=quality,
            biomarker=biomarkers[metric_name],
        )
        measurements.append(measurement)
        observations.append(observation)
        state.add_observation(observation)
        state.set_dimension(metric_name, value)

    return CellPipelineResult(
        mask=mask,
        analysis=analysis,
        measurements=measurements,
        observations=observations,
        state=state,
    )
