from __future__ import annotations

"""Canonical provenance-first multiscale anatomy for the digital hand twin."""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .data_foundation import Quality, SpatialReference, Uncertainty, Provenance

AnatomyKind = Literal["skin", "fat", "tendon", "muscle", "nerve", "vessel", "bone", "other"]
GeometryKind = Literal["point", "curve", "surface", "volume", "mesh", "segmentation"]
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
        if not self.transform: raise ValueError("registration requires a transform")
        self.quality.validate(); self.uncertainty.validate()

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
        if isinstance(self.confidence, SpatialReference):
            object.__setattr__(self, "spatial_reference", self.confidence)
            object.__setattr__(self, "confidence", None)
    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError("confidence must be between 0 and 1")
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
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError("confidence must be between 0 and 1")
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
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError("confidence must be between 0 and 1")
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
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError("confidence must be between 0 and 1")
        self.spatial_reference.validate()

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_data_ids: tuple[str, ...]
    kind: str
    value: Any
    confidence: float | None = None
    provenance: Provenance = field(default_factory=Provenance)

@dataclass(frozen=True)
class CellStateAssessment:
    assessment_id: str
    cell_id: str
    state: CellState
    confidence: float | None
    evidence: tuple[Evidence, ...]
    provenance: Provenance
    assessed_at: str
    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1: raise ValueError("confidence must be between 0 and 1")

@dataclass(frozen=True)
class MultiscaleHierarchy:
    """Canonical containment graph: hand -> structure -> tissue -> cell."""
    hand_id: str
    structures: tuple[AnatomicalStructure, ...] = ()
    tissues: tuple[TissueRegion, ...] = ()
    histology_regions: tuple[HistologyRegion, ...] = ()
    cells: tuple[CellObject, ...] = ()

    def validate(self) -> None:
        structure_ids = {item.structure_id for item in self.structures}
        tissue_ids = {item.tissue_id for item in self.tissues}
        for item in self.structures:
            item.validate()
            if item.hand_id != self.hand_id: raise ValueError("structure belongs to a different hand")
        for item in self.tissues:
            item.validate()
            if item.anatomical_structure_id not in structure_ids: raise ValueError("tissue references unknown anatomical structure")
            if item.hand_id != self.hand_id: raise ValueError("tissue belongs to a different hand")
        for item in self.histology_regions:
            item.validate()
            if item.tissue_id not in tissue_ids: raise ValueError("histology region references unknown tissue")
        for item in self.cells:
            item.validate()
            if item.tissue_id not in tissue_ids: raise ValueError("cell references unknown tissue")
            if item.hand_id != self.hand_id: raise ValueError("cell belongs to a different hand")

    def cells_for_tissue(self, tissue_id: str) -> tuple[CellObject, ...]:
        self.validate()
        return tuple(cell for cell in self.cells if cell.tissue_id == tissue_id)

    def tissues_for_structure(self, structure_id: str) -> tuple[TissueRegion, ...]:
        self.validate()
        return tuple(tissue for tissue in self.tissues if tissue.anatomical_structure_id == structure_id)

def to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "validate"): value.validate()
    return asdict(value)

def validate_multiscale_chain(anatomy: AnatomicalStructure, tissue: TissueRegion, cell: CellObject | None = None) -> None:
    if tissue.anatomical_structure_id != anatomy.structure_id: raise ValueError("tissue is not linked to the supplied anatomical structure")
    if (tissue.subject_id, tissue.hand_id, tissue.timepoint_id) != (anatomy.subject_id, anatomy.hand_id, anatomy.timepoint_id): raise ValueError("anatomy and tissue belong to different subject/hand/timepoint")
    if cell is not None and (cell.tissue_id != tissue.tissue_id or (cell.subject_id, cell.hand_id, cell.timepoint_id) != (tissue.subject_id, tissue.hand_id, tissue.timepoint_id)): raise ValueError("cell is not linked to the supplied tissue/timepoint")
