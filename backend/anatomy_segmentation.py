from __future__ import annotations

"""Phase B: modality -> anatomical structure segmentation contract.

This module deliberately separates segmentation evidence from the resulting
anatomical object. It does not claim clinical accuracy or perform diagnosis.
"""

from dataclasses import dataclass, field
from typing import Any

from .anatomy_foundation import AnatomicalStructure, Geometry
from .data_foundation import Provenance, Quality, SpatialReference, Uncertainty

SUPPORTED_MODALITIES = {"mri", "ultrasound", "ct", "3d_scan"}
SUPPORTED_ANATOMY = {"skin", "fat", "tendon", "muscle", "nerve", "vessel", "bone", "other"}


@dataclass(frozen=True)
class SegmentationEvidence:
    segmentation_id: str
    source_data_ids: tuple[str, ...]
    modality: str
    target_identity: str
    source_frame: str
    geometry: Geometry
    algorithm: str
    algorithm_version: str | None = None
    quality: Quality = field(default_factory=Quality)
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    provenance: Provenance = field(default_factory=Provenance)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.modality not in SUPPORTED_MODALITIES:
            raise ValueError(f"unsupported segmentation modality: {self.modality}")
        if self.target_identity not in SUPPORTED_ANATOMY:
            raise ValueError(f"unsupported anatomical identity: {self.target_identity}")
        if not self.source_data_ids:
            raise ValueError("segmentation must reference source data")
        if not self.algorithm.strip():
            raise ValueError("segmentation algorithm is required")
        self.quality.validate()
        self.uncertainty.validate()


def segmentation_to_anatomy(
    evidence: SegmentationEvidence,
    *,
    structure_id: str,
    subject_id: str,
    hand_id: str,
    timepoint_id: str,
    hand_frame: str,
    registration_id: str,
    confidence: float | None = None,
) -> AnatomicalStructure:
    """Create an anatomical structure from explicit segmentation evidence.

    The caller must supply the registration that placed the source modality in
    hand space; this function does not silently invent a transform.
    """
    evidence.validate()
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    spatial = SpatialReference(
        frame_id=hand_frame,
        registration_status="registered",
        transform={"registration_id": registration_id},
    )
    return AnatomicalStructure(
        structure_id=structure_id,
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        anatomical_identity=evidence.target_identity,
        geometry=evidence.geometry,
        source_data_ids=evidence.source_data_ids,
        confidence=confidence,
        spatial_reference=spatial,
        provenance=evidence.provenance,
        metadata={"segmentation_id": evidence.segmentation_id, "modality": evidence.modality, **evidence.metadata},
    )
