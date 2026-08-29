from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MicroscopyImage:
    image_id: str
    tissue_id: str
    spatial_id: str
    format: str
    width_px: int
    height_px: int
    microns_per_pixel: float
    source_id: str
    provenance_id: str
    timepoint_id: str
    qc_status: str = "unknown"

    def validate(self) -> None:
        if self.width_px <= 0 or self.height_px <= 0 or self.microns_per_pixel <= 0:
            raise ValueError("image dimensions and scale must be positive")


@dataclass(frozen=True)
class CellInstance:
    cell_id: str
    spatial_id: str
    image_id: str
    segmentation_id: str
    centroid_um: tuple[float, float]
    boundary_ref: str | None = None
    nucleus_ref: str | None = None
    confidence: float | None = None

    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class CellIdentity:
    cell_id: str
    subject_id: str
    hand_id: str
    tissue_id: str
    timepoint_id: str
    segmentation_id: str
    spatial_id: str
    neighbor_cell_ids: tuple[str, ...] = ()
    lineage_parent_id: str | None = None


@dataclass(frozen=True)
class CellTypeAssessment:
    cell_id: str
    cell_type: str
    confidence: float | None = None
    morphology_features: dict[str, float] = field(default_factory=dict)
    marker_refs: tuple[str, ...] = ()
    molecular_refs: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    model_id: str | None = None
    model_version: str | None = None
    validation_status: str = "not_validated"

    def validate(self) -> None:
        if not self.cell_id or not self.cell_type:
            raise ValueError("cell_id and cell_type are required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
