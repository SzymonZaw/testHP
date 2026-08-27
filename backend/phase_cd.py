from __future__ import annotations

"""Phase C/D domain contracts: anatomy and tissue evidence pipelines."""

from dataclasses import dataclass, field
from typing import Any, Literal

from .anatomy_foundation import AnatomicalStructure, HistologyRegion, TissueRegion
from .anatomy_segmentation import SegmentationEvidence
from .spatial_registration import RegistrationInput, build_registration
from .tissue_histology import TissueEvidence, tissue_from_anatomy
from .data_foundation import Provenance, Quality, SpatialReference, Uncertainty

PathologyState = Literal["normal", "atypical", "inflammatory", "fibrotic", "degenerative", "neoplastic", "unknown"]


@dataclass(frozen=True)
class MultimodalEvidence:
    evidence_id: str
    source_data_ids: tuple[str, ...]
    modality: str
    anatomical_target: str
    observations: dict[str, Any]
    quality: Quality = field(default_factory=Quality)
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if not self.source_data_ids:
            raise ValueError("multimodal evidence requires source data")
        if not self.anatomical_target:
            raise ValueError("anatomical target is required")
        self.quality.validate()
        self.uncertainty.validate()


@dataclass(frozen=True)
class TissuePathologyAssessment:
    assessment_id: str
    tissue_id: str
    state: PathologyState
    findings: dict[str, Any]
    evidence: tuple[str, ...]
    confidence: float | None
    provenance: Provenance
    assessed_at: str

    def validate(self) -> None:
        if not self.evidence:
            raise ValueError("tissue pathology assessment requires evidence")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


def register_multimodal(value: RegistrationInput):
    """Validate and create the canonical multimodal registration result."""
    return build_registration(value)


def create_tissue(evidence: TissueEvidence, *, subject_id: str, hand_id: str, timepoint_id: str) -> TissueRegion:
    return tissue_from_anatomy(evidence, subject_id=subject_id, hand_id=hand_id, timepoint_id=timepoint_id)


def assess_tissue_pathology(*, assessment_id: str, tissue: TissueRegion, state: PathologyState, findings: dict[str, Any], evidence: tuple[str, ...], confidence: float | None, assessed_at: str, provenance: Provenance) -> TissuePathologyAssessment:
    assessment = TissuePathologyAssessment(assessment_id, tissue.tissue_id, state, findings, evidence, confidence, provenance, assessed_at)
    assessment.validate()
    return assessment
