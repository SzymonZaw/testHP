from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .anatomy_foundation import CellObject, CellStateAssessment, Evidence
from .data_foundation import Provenance, SpatialReference


@dataclass(frozen=True)
class CellObservation:
    """One auditable observation of a cell at one acquisition timepoint.

    This object stores measured/derived observations and their provenance. It
    deliberately does not decide whether a cell is healthy or prescribe care.
    """

    observation_id: str
    cell_id: str
    subject_id: str
    hand_id: str
    tissue_id: str
    timepoint_id: str
    modality: str
    source_data_ids: tuple[str, ...]
    spatial_reference: SpatialReference
    measurements: dict[str, Any] = field(default_factory=dict)
    evidence: tuple[Evidence, ...] = ()
    assessment: CellStateAssessment | None = None
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if not self.observation_id or not self.cell_id or not self.subject_id or not self.hand_id:
            raise ValueError("cell observation identity is required")
        if not self.tissue_id or not self.timepoint_id or not self.modality:
            raise ValueError("cell observation context is required")
        if not self.source_data_ids:
            raise ValueError("cell observation requires source data")
        self.spatial_reference.validate()
        for item in self.evidence:
            if hasattr(item, "validate"):
                item.validate()
        if self.assessment is not None:
            if self.assessment.cell_id != self.cell_id:
                raise ValueError("cell assessment must match observation cell")
            self.assessment.validate()

    def matches_cell(self, cell: CellObject) -> bool:
        return (
            self.cell_id,
            self.subject_id,
            self.hand_id,
            self.tissue_id,
            self.timepoint_id,
        ) == (
            cell.cell_id,
            cell.subject_id,
            cell.hand_id,
            cell.tissue_id,
            cell.timepoint_id,
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "observation_id": self.observation_id,
            "cell_id": self.cell_id,
            "subject_id": self.subject_id,
            "hand_id": self.hand_id,
            "tissue_id": self.tissue_id,
            "timepoint_id": self.timepoint_id,
            "modality": self.modality,
            "source_data_ids": list(self.source_data_ids),
            "spatial_reference": self.spatial_reference.__dict__.copy(),
            "measurements": dict(self.measurements),
            "evidence": [item.__dict__.copy() for item in self.evidence],
            "assessment": self.assessment.__dict__.copy() if self.assessment is not None else None,
            "provenance": self.provenance.__dict__.copy(),
        }


def build_cell_observation(
    cell: CellObject,
    *,
    observation_id: str,
    modality: str,
    source_data_ids: tuple[str, ...],
    measurements: dict[str, Any] | None = None,
    evidence: tuple[Evidence, ...] = (),
    assessment: CellStateAssessment | None = None,
    provenance: Provenance | None = None,
) -> CellObservation:
    """Create an observation anchored to an existing cell identity."""
    observation = CellObservation(
        observation_id=observation_id,
        cell_id=cell.cell_id,
        subject_id=cell.subject_id,
        hand_id=cell.hand_id,
        tissue_id=cell.tissue_id,
        timepoint_id=cell.timepoint_id,
        modality=modality,
        source_data_ids=source_data_ids,
        spatial_reference=cell.spatial_reference,
        measurements=measurements or {},
        evidence=evidence,
        assessment=assessment,
        provenance=provenance or Provenance(),
    )
    observation.validate()
    return observation
