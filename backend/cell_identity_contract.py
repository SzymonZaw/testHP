from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .spatial_contract import canonical_spatial_id

@dataclass(frozen=True)
class CellIdentity:
    cell_id: str
    subject_id: str
    hand_id: str
    tissue_id: str
    timepoint_id: str
    segmentation_id: str
    spatial_id: str
    centroid_um: tuple[float, float, float] | None = None
    neighbor_cell_ids: tuple[str, ...] = ()
    lineage_parent_id: str | None = None

    def validate(self) -> None:
        if not all((self.cell_id, self.subject_id, self.hand_id, self.tissue_id, self.timepoint_id, self.segmentation_id)):
            raise ValueError("cell identity is incomplete")
        canonical_spatial_id(self.spatial_id)
        if self.centroid_um is not None and len(self.centroid_um) != 3:
            raise ValueError("centroid_um must contain x, y and z")

@dataclass(frozen=True)
class CellTypeAssessment:
    cell_id: str
    cell_type: str
    confidence: float | None
    morphology_features: dict[str, Any] = field(default_factory=dict)
    marker_evidence_ids: tuple[str, ...] = ()
    molecular_evidence_ids: tuple[str, ...] = ()
    model_id: str | None = None
    model_version: str | None = None

    def validate(self) -> None:
        if not self.cell_id or not self.cell_type:
            raise ValueError("cell type assessment identity is incomplete")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("cell type confidence must be between 0 and 1")
