from __future__ import annotations

"""Phase C contracts for cell observations and model-derived interpretation.

This module intentionally does not diagnose disease. Predictions are claims
with explicit evidence, uncertainty, model identity and provenance.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from .anatomy_foundation import CellObject
from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence
from .data_foundation import Provenance, Uncertainty

PredictionState = Literal["normal", "atypical", "suspicious", "pathological", "indeterminate"]


@dataclass(frozen=True)
class CellObservation:
    observation_id: str
    cell_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    source_object_ids: tuple[str, ...]
    features: dict[str, Any]
    spatial_reference_frame: str
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if not self.observation_id.strip() or not self.cell_id.strip():
            raise ValueError("observation_id and cell_id are required")
        if not self.source_object_ids:
            raise ValueError("cell observation requires source_object_ids")
        if not self.features:
            raise ValueError("cell observation requires features")
        if not self.spatial_reference_frame.strip():
            raise ValueError("cell observation requires a spatial reference frame")


@dataclass(frozen=True)
class CellFeatureSet:
    feature_set_id: str
    observation_id: str
    features: dict[str, float]
    extractor_id: str
    extractor_version: str
    provenance: Provenance

    def validate(self) -> None:
        if not self.features:
            raise ValueError("feature set cannot be empty")
        if not self.extractor_id.strip() or not self.extractor_version.strip():
            raise ValueError("feature extractor identity and version are required")


@dataclass(frozen=True)
class CellStatePrediction:
    prediction_id: str
    cell_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    state: PredictionState
    confidence: float
    uncertainty: Uncertainty
    evidence: tuple[InterpretationEvidence, ...]
    model_id: str
    model_version: str
    assessed_at: str
    provenance: Provenance

    def validate(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("prediction confidence must be between 0 and 1")
        if not self.model_id.strip() or not self.model_version.strip():
            raise ValueError("model identity and version are required")
        if not self.evidence:
            raise ValueError("cell state prediction requires evidence")
        for item in self.evidence:
            item.validate()
        self.uncertainty.validate()

    def to_assessment(self) -> BiologicalStateAssessment:
        self.validate()
        assessment = BiologicalStateAssessment(
            assessment_id=self.prediction_id,
            subject_id=self.subject_id,
            hand_id=self.hand_id,
            timepoint_id=self.timepoint_id,
            target_object_id=self.cell_id,
            state=self.state,
            confidence=self.confidence,
            evidence=self.evidence,
            uncertainty=self.uncertainty,
            provenance=self.provenance,
            assessed_at=self.assessed_at,
            model_id=self.model_id,
            model_version=self.model_version,
            metadata={"prediction_id": self.prediction_id},
        )
        assessment.validate()
        return assessment


def observation_from_cell(cell: CellObject, observation_id: str, *, source_object_ids: tuple[str, ...] | None = None) -> CellObservation:
    cell.validate()
    sources = source_object_ids or cell.source_data_ids
    return CellObservation(
        observation_id=observation_id,
        cell_id=cell.cell_id,
        subject_id=cell.subject_id,
        hand_id=cell.hand_id,
        timepoint_id=cell.timepoint_id,
        source_object_ids=tuple(sources),
        features={**cell.morphology, **{f"size.{k}": v for k, v in cell.size.items()}, **{f"nucleus.{k}": v for k, v in cell.nucleus.items()}},
        spatial_reference_frame=cell.spatial_reference.frame_id,
        provenance=cell.provenance,
    )


def make_prediction(
    *,
    prediction_id: str,
    cell: CellObject,
    observation: CellObservation,
    state: PredictionState,
    confidence: float,
    uncertainty: Uncertainty,
    model_id: str,
    model_version: str,
    assessed_at: str,
) -> CellStatePrediction:
    observation.validate()
    if observation.cell_id != cell.cell_id or observation.timepoint_id != cell.timepoint_id:
        raise ValueError("observation does not belong to the supplied cell/timepoint")
    evidence = InterpretationEvidence(
        evidence_id=f"{prediction_id}:observation",
        source_object_ids=(observation.observation_id,),
        kind="cell_features",
        value=observation.features,
        confidence=confidence,
        provenance=observation.provenance,
    )
    return CellStatePrediction(
        prediction_id=prediction_id,
        cell_id=cell.cell_id,
        subject_id=cell.subject_id,
        hand_id=cell.hand_id,
        timepoint_id=cell.timepoint_id,
        state=state,
        confidence=confidence,
        uncertainty=uncertainty,
        evidence=(evidence,),
        model_id=model_id,
        model_version=model_version,
        assessed_at=assessed_at,
        provenance=Provenance(
            source_object_ids=(observation.observation_id,),
            method=model_id,
            method_version=model_version,
        ),
    )
