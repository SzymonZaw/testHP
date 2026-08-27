from __future__ import annotations

"""Phase E/F: cell and molecular-data contracts.

These objects represent observations and provenance. They do not make clinical
or biological diagnoses on their own.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from .data_foundation import Provenance, SpatialReference, Quality, Uncertainty

CellState = Literal["normal", "stressed", "senescent", "apoptotic", "proliferating", "inflammatory", "pathological", "unknown"]
OmicsModality = Literal["scRNA-seq", "spatial-transcriptomics", "proteomics", "epigenetics"]


@dataclass(frozen=True)
class CellIdentity:
    cell_id: str
    cell_type: str | None
    markers: dict[str, float] = field(default_factory=dict)
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.evidence_ids:
            raise ValueError("cell identity requires evidence")


@dataclass(frozen=True)
class CellMorphology:
    cell_id: str
    measurements: dict[str, float]
    nucleus_measurements: dict[str, float] = field(default_factory=dict)
    shape_features: dict[str, float] = field(default_factory=dict)
    segmentation_quality: float | None = None
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.measurements:
            raise ValueError("cell morphology requires measurements")
        if not self.evidence_ids:
            raise ValueError("cell morphology requires evidence")


@dataclass(frozen=True)
class CellState:
    assessment_id: str
    cell_id: str
    state: CellState
    confidence: float | None
    evidence_ids: tuple[str, ...]
    provenance: Provenance
    assessed_at: str

    def validate(self) -> None:
        if not self.evidence_ids:
            raise ValueError("cell state requires evidence")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class MolecularAssay:
    assay_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    modality: OmicsModality
    source_data_ids: tuple[str, ...]
    sample_id: str
    feature_space: str
    measurements: dict[str, Any] = field(default_factory=dict)
    spatial_reference: SpatialReference | None = None
    quality: Quality = field(default_factory=Quality)
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    provenance: Provenance = field(default_factory=Provenance)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_data_ids:
            raise ValueError("molecular assay requires source data")
        if not self.sample_id:
            raise ValueError("molecular assay requires sample_id")
        if not self.feature_space:
            raise ValueError("molecular assay requires feature_space")
        if self.spatial_reference:
            self.spatial_reference.validate()
        self.quality.validate()
        self.uncertainty.validate()


@dataclass(frozen=True)
class MultiOmicsLink:
    integration_id: str
    assay_ids: tuple[str, ...]
    subject_id: str
    hand_id: str
    timepoint_id: str
    alignment_space: str
    cell_or_region_ids: tuple[str, ...] = ()
    method: str = ""
    confidence: float | None = None
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if len(self.assay_ids) < 2:
            raise ValueError("multi-omics integration requires at least two assays")
        if not self.alignment_space:
            raise ValueError("multi-omics integration requires an alignment space")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
