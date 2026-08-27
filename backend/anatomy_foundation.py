from __future__ import annotations

"""Phase B: multimodal anatomy, spatial registration, tissue and cell domain.

These are provenance-first data objects. They describe evidence and derived
representations; they do not make clinical diagnoses or treatment decisions.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .data_foundation import Quality, SpatialReference, Uncertainty, Provenance

AnatomyKind = Literal["skin", "fat", "tendon", "muscle", "nerve", "vessel", "bone", "other"]
GeometryKind = Literal["point", "curve", "surface", "volume", "mesh", "segmentation"]
Modality = Literal["photo", "3d_scan", "mri", "ultrasound", "ct", "other"]
CellState = Literal["normal", "stressed", "senescent", "apoptotic", "proliferating", "inflammatory", "pathological", "unknown"]


@dataclass(frozen=True)
class HandCoordinateSystem:
    frame_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str = "unknown"
    axes: dict[str, Any] = field(default_factory=dict)
    origin_landmark: str | None = None
    units: str = "mm"
    version: str = "1"


@dataclass(frozen=True)
class Registration:
    registration_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    source_frame: str
    target_frame: str
    modality: str
    transform: dict[str, Any]
    quality: Quality = field(default_factory=Quality)
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    method: str | None = None
    method_version: str | None = None
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if not self.transform:
            raise ValueError("registration requires a transform")
        self.quality.validate()
        self.uncertainty.validate()


@dataclass(frozen=True)
class Geometry:
    geometry_id: str
    kind: GeometryKind
    reference_frame: str
    uri: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnatomicalStructure:
    structure_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    anatomical_identity: AnatomyKind
    geometry: Geometry
    source_data_ids: tuple[str, ...]
    confidence: float | None = None
    spatial_reference: SpatialReference = field(default_factory=lambda: SpatialReference("unknown"))
    provenance: Provenance = field(default_factory=Provenance)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Compatibility with the historical positional constructor where the
        # spatial reference occupied the slot now used by confidence.
        if isinstance(self.confidence, SpatialReference):
            object.__setattr__(self, "spatial_reference", self.confidence)
            object.__setattr__(self, "confidence", None)

    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.spatial_reference.validate()


@dataclass(frozen=True)
class TissueRegion:
    tissue_id: str
    anatomical_structure_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    tissue_type: str
    geometry: Geometry
    source_data_ids: tuple[str, ...]
    spatial_reference: SpatialReference
    confidence: float | None = None
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.spatial_reference.validate()


@dataclass(frozen=True)
class HistologyRegion:
    histology_id: str
    tissue_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    method: str
    image_data_id: str
    region_geometry: Geometry
    spatial_reference: SpatialReference
    confidence: float | None = None
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.spatial_reference.validate()


@dataclass(frozen=True)
class CellObject:
    cell_id: str
    tissue_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    position: dict[str, float]
    cell_type: str | None
    morphology: dict[str, Any]
    size: dict[str, float]
    nucleus: dict[str, Any]
    neighbors: tuple[str, ...]
    source_data_ids: tuple[str, ...]
    spatial_reference: SpatialReference
    confidence: float | None = None
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.spatial_reference.validate()


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
