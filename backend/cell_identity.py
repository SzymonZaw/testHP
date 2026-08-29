from __future__ import annotations

"""Canonical cell identity and typing primitives.

Cell IDs are stable within a subject/hand/tissue/timepoint namespace. They do
not encode a health judgement or diagnosis.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CellIdentity:
    cell_id: str
    subject_id: str
    hand_id: str
    tissue_id: str
    timepoint_id: str
    segmentation_id: str
    instance_index: int
    centroid: dict[str, float] = field(default_factory=dict)
    cell_type: str | None = None
    cell_type_confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        required = (self.cell_id, self.subject_id, self.hand_id, self.tissue_id,
                    self.timepoint_id, self.segmentation_id)
        if not all(required):
            raise ValueError("cell identity context is required")
        if self.instance_index < 0:
            raise ValueError("instance_index must be non-negative")
        if self.cell_type_confidence is not None and not 0 <= self.cell_type_confidence <= 1:
            raise ValueError("cell type confidence must be between 0 and 1")


def make_cell_id(subject_id: str, hand_id: str, tissue_id: str,
                 timepoint_id: str, segmentation_id: str,
                 instance_index: int) -> str:
    if instance_index < 0:
        raise ValueError("instance_index must be non-negative")
    return ":".join((str(subject_id), str(hand_id), str(tissue_id),
                     str(timepoint_id), str(segmentation_id),
                     f"cell-{instance_index:06d}"))


def build_cell_identity(**kwargs: Any) -> CellIdentity:
    cell = CellIdentity(**kwargs)
    cell.validate()
    return cell
