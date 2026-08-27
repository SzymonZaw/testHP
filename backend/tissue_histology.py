from __future__ import annotations

"""Phase B: tissue and histology binding contracts."""

from dataclasses import dataclass, field
from typing import Any

from .anatomy_foundation import Geometry, HistologyRegion, TissueRegion
from .data_foundation import Provenance, SpatialReference

HISTOLOGY_METHODS = {"H&E", "immunohistochemistry", "immunofluorescence", "other"}


@dataclass(frozen=True)
class TissueEvidence:
    tissue_id: str
    anatomical_structure_id: str
    source_data_ids: tuple[str, ...]
    tissue_type: str
    geometry: Geometry
    spatial_reference: SpatialReference
    confidence: float | None = None
    provenance: Provenance = field(default_factory=Provenance)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_data_ids:
            raise ValueError("tissue evidence must reference source data")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.spatial_reference.validate()


def tissue_from_anatomy(evidence: TissueEvidence, *, subject_id: str, hand_id: str, timepoint_id: str) -> TissueRegion:
    evidence.validate()
    return TissueRegion(
        tissue_id=evidence.tissue_id,
        anatomical_structure_id=evidence.anatomical_structure_id,
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        tissue_type=evidence.tissue_type,
        geometry=evidence.geometry,
        source_data_ids=evidence.source_data_ids,
        spatial_reference=evidence.spatial_reference,
        confidence=evidence.confidence,
        provenance=evidence.provenance,
    )


def bind_histology(
    *,
    histology_id: str,
    tissue: TissueRegion,
    image_data_id: str,
    method: str,
    region_geometry: Geometry,
    spatial_reference: SpatialReference,
    confidence: float | None = None,
    provenance: Provenance | None = None,
) -> HistologyRegion:
    if method not in HISTOLOGY_METHODS:
        raise ValueError(f"unsupported histology method: {method}")
    if not image_data_id.strip():
        raise ValueError("histology requires an image data object")
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    spatial_reference.validate()
    return HistologyRegion(
        histology_id=histology_id,
        tissue_id=tissue.tissue_id,
        subject_id=tissue.subject_id,
        hand_id=tissue.hand_id,
        timepoint_id=tissue.timepoint_id,
        method=method,
        image_data_id=image_data_id,
        region_geometry=region_geometry,
        spatial_reference=spatial_reference,
        confidence=confidence,
        provenance=provenance or Provenance(),
    )
