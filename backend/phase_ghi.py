from __future__ import annotations

"""Phases G-I: longitudinal twin state and clinical-governance contracts.

These are evidence/inference boundaries, not medical diagnosis or treatment
engines. Predictions must retain their source observations and uncertainty.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from .data_foundation import Provenance, Uncertainty

TrajectoryKind = Literal["aging", "disease"]
InterventionMode = Literal["observe", "review", "simulate", "candidate"]
ValidationStatus = Literal["unvalidated", "research", "externally_validated", "clinical_validated"]


@dataclass(frozen=True)
class LongitudinalObservation:
    observation_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    timestamp: str
    feature_space: str
    values: dict[str, Any]
    source_ids: tuple[str, ...]
    provenance: Provenance


@dataclass(frozen=True)
class BiologicalAgeEstimate:
    estimate_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    age_scale: str
    estimate: float
    uncertainty: Uncertainty
    source_ids: tuple[str, ...]
    model_id: str
    model_version: str
    validation_status: ValidationStatus = "unvalidated"

    def validate(self) -> None:
        if not self.source_ids:
            raise ValueError("biological age requires source observations")
        if not self.model_id or not self.model_version:
            raise ValueError("biological age requires model identity and version")
        self.uncertainty.validate()


@dataclass(frozen=True)
class Trajectory:
    trajectory_id: str
    subject_id: str
    hand_id: str
    kind: TrajectoryKind
    observation_ids: tuple[str, ...]
    feature_space: str
    model_id: str | None = None
    confidence: float | None = None
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if len(self.observation_ids) < 2:
            raise ValueError("trajectory requires at least two observations")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class SpatialModel:
    model_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    reference_frame: str
    object_ids: tuple[str, ...]
    scales: tuple[str, ...]
    registration_ids: tuple[str, ...]


@dataclass(frozen=True)
class CrossScaleLink:
    link_id: str
    parent_id: str
    child_id: str
    relation: str
    transform_or_mapping: dict[str, Any]
    evidence_ids: tuple[str, ...]

    def validate(self) -> None:
        if not self.evidence_ids:
            raise ValueError("cross-scale link requires evidence")


@dataclass(frozen=True)
class StateEstimate:
    estimate_id: str
    target_id: str
    timepoint_id: str
    state_vector: dict[str, Any]
    source_ids: tuple[str, ...]
    uncertainty: Uncertainty
    model_id: str
    model_version: str


@dataclass(frozen=True)
class WhatIfScenario:
    scenario_id: str
    base_state_ids: tuple[str, ...]
    interventions: tuple[dict[str, Any], ...]
    assumptions: tuple[str, ...]
    outputs: dict[str, Any] = field(default_factory=dict)
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    status: Literal["proposed", "simulated", "review_required"] = "proposed"


@dataclass(frozen=True)
class RiskAssessment:
    assessment_id: str
    subject_id: str
    timepoint_id: str
    risk_target: str
    risk_score: float
    horizon: str
    source_ids: tuple[str, ...]
    uncertainty: Uncertainty
    model_id: str
    model_version: str
    validation_status: ValidationStatus = "unvalidated"

    def validate(self) -> None:
        if not self.source_ids:
            raise ValueError("risk assessment requires evidence")
        if not 0 <= self.risk_score <= 1:
            raise ValueError("risk score must be between 0 and 1")
        self.uncertainty.validate()


@dataclass(frozen=True)
class InterventionSupport:
    support_id: str
    risk_assessment_id: str
    mode: InterventionMode
    options: tuple[dict[str, Any], ...]
    evidence_ids: tuple[str, ...]
    clinician_review_required: bool = True


@dataclass(frozen=True)
class ValidationRecord:
    validation_id: str
    model_id: str
    model_version: str
    dataset_id: str
    cohort_description: str
    metrics: dict[str, float]
    validation_status: ValidationStatus
    protocol_version: str
    reviewer: str | None = None


@dataclass(frozen=True)
class ClinicalRegulatoryRecord:
    record_id: str
    model_id: str
    intended_use: str
    contraindications: tuple[str, ...]
    human_oversight: str
    audit_trail_ids: tuple[str, ...]
    data_governance: dict[str, Any]
    regulatory_status: str

    def validate(self) -> None:
        if not self.intended_use or not self.human_oversight:
            raise ValueError("clinical/regulatory record requires intended use and human oversight")
        if not self.audit_trail_ids:
            raise ValueError("clinical/regulatory record requires audit trail")
