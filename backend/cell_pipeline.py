from __future__ import annotations

"""Phase B: microscopy -> cell objects -> evidence-backed cell state."""

from dataclasses import dataclass
from typing import Any

from .anatomy_foundation import CellObject, CellStateAssessment, Evidence
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
        if not self.tissue_id:
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
) -> CellObject:
    evidence.validate()
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if cell_record not in evidence.cells:
        raise ValueError("cell record is not part of the supplied segmentation evidence")
    return CellObject(
        cell_id=str(cell_record["cell_id"]),
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
        spatial_reference=SpatialReference(hand_frame, "registered", {"segmentation_id": evidence.segmentation_id}),
        confidence=confidence,
        provenance=Provenance(source_data_ids=evidence.source_data_ids, method=evidence.algorithm, method_version=evidence.algorithm_version),
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
    assessment = CellStateAssessment(assessment_id, cell.cell_id, state, confidence, evidence, provenance, assessed_at)
    assessment.validate()
    return assessment
