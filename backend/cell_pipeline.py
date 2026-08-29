from __future__ import annotations

"""Canonical Phase C/D adapter: segmentation -> cell observation -> assessment.

This module keeps the existing CellObject/CellStateAssessment contract as the
compatibility boundary while exposing deterministic cell IDs and typed health
outputs. No biological inference is performed here.
"""

from dataclasses import dataclass
from typing import Any

from .anatomy_foundation import CellObject, CellStateAssessment, Evidence
from .cell_identity import make_cell_id
from .data_foundation import Provenance, SpatialReference


@dataclass(frozen=True)
class CellSegmentationEvidence:
    segmentation_id: str
    tissue_id: str
    source_data_ids: tuple[str, ...]
    cells: tuple[dict[str, Any], ...]
    algorithm: str
    algorithm_version: str | None = None

    def validate(self) -> None:
        if not self.segmentation_id.strip():
            raise ValueError("cell segmentation requires segmentation_id")
        if not self.tissue_id.strip():
            raise ValueError("cell segmentation requires tissue_id")
        if not self.source_data_ids:
            raise ValueError("cell segmentation must reference source data")
        if not self.algorithm.strip():
            raise ValueError("cell segmentation algorithm is required")


def cell_from_segmentation(
    evidence: CellSegmentationEvidence,
    cell_record: dict[str, Any],
    *,
    subject_id: str,
    hand_id: str,
    timepoint_id: str,
    hand_frame: str,
    confidence: float | None = None,
    instance_index: int | None = None,
) -> CellObject:
    evidence.validate()
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")

    cell_id = str(cell_record.get("cell_id", "")).strip()
    if not cell_id:
        if instance_index is None:
            raise ValueError("cell record requires cell_id or instance_index")
        cell_id = make_cell_id(
            subject_id, hand_id, evidence.tissue_id, timepoint_id,
            evidence.segmentation_id, instance_index,
        )

    if not any(str(record.get("cell_id", "")).strip() == cell_id for record in evidence.cells):
        # A generated ID is valid when the segmentation record identifies the
        # same instance by index.
        if instance_index is None or not any(
            int(record.get("instance_index", -1)) == instance_index
            for record in evidence.cells
        ):
            raise ValueError("cell record is not part of supplied segmentation evidence")

    return CellObject(
        cell_id=cell_id,
        tissue_id=evidence.tissue_id,
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        position=dict(cell_record.get("position", {})),
        cell_type=cell_record.get("cell_type"),
        morphology=dict(cell_record.get("morphology", {})),
        size=dict(cell_record.get("size", {})),
        nucleus=dict(cell_record.get("nucleus", {})),
        neighbors=tuple(cell_record.get("neighbors", ())),
        source_data_ids=evidence.source_data_ids,
        spatial_reference=SpatialReference(
            hand_frame, "registered", {"segmentation_id": evidence.segmentation_id}
        ),
        confidence=confidence,
        provenance=Provenance(
            source_object_ids=evidence.source_data_ids,
            method=evidence.algorithm,
            method_version=evidence.algorithm_version,
        ),
    )


def assess_cell_state(
    *,
    assessment_id: str,
    cell: CellObject,
    state: str,
    evidence: tuple[Evidence, ...],
    confidence: float | None,
    assessed_at: str,
    provenance: Provenance,
) -> CellStateAssessment:
    assessment = CellStateAssessment(
        assessment_id, cell.cell_id, state, confidence,
        evidence, provenance, assessed_at,
    )
    assessment.validate()
    return assessment
