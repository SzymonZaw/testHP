from __future__ import annotations

"""Phase C: tissue-level aggregation of cell observations and predictions.

This module summarizes cell-level evidence into a tissue profile. It is not a
clinical diagnosis or treatment recommendation; every summary keeps explicit
lineage, uncertainty and model-independent aggregate metrics.
"""

from dataclasses import dataclass, field
from typing import Any

from .anatomy_foundation import CellObject, TissueRegion
from .biological_state import BiologicalStateAssessment, InterpretationEvidence
from .cell_intelligence import CellStatePrediction, observation_from_cell
from .data_foundation import Provenance, Uncertainty


@dataclass(frozen=True)
class TissueObservation:
    observation_id: str
    tissue_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    cell_count: int
    state_counts: dict[str, int]
    state_fractions: dict[str, float]
    feature_means: dict[str, float]
    source_object_ids: tuple[str, ...]
    spatial_reference_frame: str
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if not self.observation_id.strip() or not self.tissue_id.strip():
            raise ValueError("observation_id and tissue_id are required")
        if self.cell_count <= 0:
            raise ValueError("tissue observation requires at least one cell")
        if self.state_counts and sum(self.state_counts.values()) != self.cell_count:
            raise ValueError("state counts must equal cell_count")
        if self.source_object_ids == ():
            raise ValueError("tissue observation requires source_object_ids")
        if not self.spatial_reference_frame.strip():
            raise ValueError("tissue observation requires a spatial reference frame")


@dataclass(frozen=True)
class TissueStateSummary:
    summary_id: str
    tissue_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    dominant_state: str
    confidence: float
    uncertainty: Uncertainty
    cell_count: int
    state_fractions: dict[str, float]
    evidence: tuple[InterpretationEvidence, ...]
    provenance: Provenance
    assessed_at: str
    model_id: str = "cell-state-aggregation"
    model_version: str = "1.0"

    def validate(self) -> None:
        if not self.summary_id.strip() or not self.tissue_id.strip():
            raise ValueError("summary_id and tissue_id are required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("summary confidence must be between 0 and 1")
        if self.cell_count <= 0:
            raise ValueError("summary requires at least one cell")
        if not self.evidence:
            raise ValueError("tissue state summary requires evidence")
        self.uncertainty.validate()
        for item in self.evidence:
            item.validate()

    def to_assessment(self) -> BiologicalStateAssessment:
        self.validate()
        assessment = BiologicalStateAssessment(
            assessment_id=self.summary_id,
            subject_id=self.subject_id,
            hand_id=self.hand_id,
            timepoint_id=self.timepoint_id,
            target_object_id=self.tissue_id,
            state=self.dominant_state,
            confidence=self.confidence,
            evidence=self.evidence,
            uncertainty=self.uncertainty,
            provenance=self.provenance,
            assessed_at=self.assessed_at,
            model_id=self.model_id,
            model_version=self.model_version,
            metadata={"cell_count": self.cell_count, "state_fractions": self.state_fractions},
        )
        assessment.validate()
        return assessment


def observe_tissue(tissue: TissueRegion, cells: tuple[CellObject, ...], observation_id: str) -> TissueObservation:
    tissue.validate()
    if not cells:
        raise ValueError("cannot observe tissue without cells")
    for cell in cells:
        cell.validate()
        if (cell.tissue_id, cell.subject_id, cell.hand_id, cell.timepoint_id) != (tissue.tissue_id, tissue.subject_id, tissue.hand_id, tissue.timepoint_id):
            raise ValueError("cell does not belong to tissue/subject/hand/timepoint")
    observations = tuple(observation_from_cell(cell, f"{observation_id}:{cell.cell_id}") for cell in cells)
    feature_values: dict[str, list[float]] = {}
    for observation in observations:
        for key, value in observation.features.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                feature_values.setdefault(key, []).append(float(value))
    means = {key: sum(values) / len(values) for key, values in feature_values.items()}
    sources = tuple(dict.fromkeys(source for item in observations for source in item.source_object_ids))
    result = TissueObservation(
        observation_id=observation_id,
        tissue_id=tissue.tissue_id,
        subject_id=tissue.subject_id,
        hand_id=tissue.hand_id,
        timepoint_id=tissue.timepoint_id,
        cell_count=len(cells),
        state_counts={},
        state_fractions={},
        feature_means=means,
        source_object_ids=sources,
        spatial_reference_frame=tissue.spatial_reference.frame_id,
        provenance=Provenance(source_object_ids=sources, method="tissue-observation", method_version="1.0"),
    )
    result.validate()
    return result


def summarize_tissue_states(tissue: TissueRegion, predictions: tuple[CellStatePrediction, ...], *, summary_id: str, assessed_at: str) -> TissueStateSummary:
    tissue.validate()
    if not predictions:
        raise ValueError("cannot summarize tissue without cell predictions")
    for prediction in predictions:
        prediction.validate()
        if (prediction.subject_id, prediction.hand_id, prediction.timepoint_id) != (tissue.subject_id, tissue.hand_id, tissue.timepoint_id):
            raise ValueError("prediction does not belong to tissue/subject/hand/timepoint")
    counts: dict[str, int] = {}
    for prediction in predictions:
        counts[prediction.state] = counts.get(prediction.state, 0) + 1
    total = len(predictions)
    fractions = {state: count / total for state, count in counts.items()}
    dominant = max(counts, key=counts.get)
    confidence = fractions[dominant]
    prediction_ids = tuple(prediction.prediction_id for prediction in predictions)
    provenance = Provenance(source_object_ids=prediction_ids, method="cell-state-aggregation", method_version="1.0")
    evidence = (InterpretationEvidence(evidence_id=f"{summary_id}:cells", source_object_ids=prediction_ids, kind="cell_state_distribution", value={"counts": counts, "fractions": fractions}, confidence=confidence, provenance=provenance),)
    return TissueStateSummary(summary_id=summary_id, tissue_id=tissue.tissue_id, subject_id=tissue.subject_id, hand_id=tissue.hand_id, timepoint_id=tissue.timepoint_id, dominant_state=dominant, confidence=confidence, uncertainty=Uncertainty(kind="distribution", score=1.0 - confidence), cell_count=total, state_fractions=fractions, evidence=evidence, provenance=provenance, assessed_at=assessed_at)
