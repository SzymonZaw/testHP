from __future__ import annotations

"""Cell-level biological interpretation primitives.

These objects separate measured features from interpretation. They are
intended for decision support and research, not autonomous diagnosis.
"""

from dataclasses import dataclass, field
from typing import Any

from .anatomy_foundation import CellObject, CellStateAssessment, Evidence
from .data_foundation import Provenance, Uncertainty


@dataclass(frozen=True)
class CellBiologicalProfile:
    cell_id: str
    morphology: dict[str, Any] = field(default_factory=dict)
    size: dict[str, float] = field(default_factory=dict)
    nucleus: dict[str, Any] = field(default_factory=dict)
    markers: dict[str, float] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    completeness: float = 0.0

    def validate(self) -> None:
        if not self.cell_id.strip():
            raise ValueError("cell_id is required")
        if not 0 <= self.completeness <= 1:
            raise ValueError("completeness must be between 0 and 1")

    @classmethod
    def from_cell(cls, cell: CellObject, *, markers: dict[str, float] | None = None, evidence_ids: tuple[str, ...] = ()) -> "CellBiologicalProfile":
        cell.validate()
        markers = markers or {}
        populated = sum(bool(value) for value in (cell.morphology, cell.size, cell.nucleus, markers))
        return cls(cell.cell_id, dict(cell.morphology), dict(cell.size), dict(cell.nucleus), dict(markers), tuple(evidence_ids), populated / 4.0)


@dataclass(frozen=True)
class CellStateAssessmentRecord:
    assessment: CellStateAssessment
    uncertainty: Uncertainty = field(default_factory=Uncertainty)

    def validate(self) -> None:
        self.assessment.validate()
        self.uncertainty.validate()
        if not self.assessment.evidence:
            raise ValueError("cell state assessment requires evidence")


def assess_profile(*, assessment_id: str, profile: CellBiologicalProfile, state: str, confidence: float | None, evidence: tuple[Evidence, ...], assessed_at: str, provenance: Provenance, uncertainty: Uncertainty | None = None) -> CellStateAssessmentRecord:
    profile.validate()
    if not evidence:
        raise ValueError("cell state assessment requires evidence")
    if any(item.evidence_id not in profile.evidence_ids for item in evidence) and profile.evidence_ids:
        raise ValueError("assessment evidence is not linked to the cell profile")
    assessment = CellStateAssessment(assessment_id, profile.cell_id, state, confidence, evidence, provenance, assessed_at)
    record = CellStateAssessmentRecord(assessment, uncertainty or Uncertainty())
    record.validate()
    return record
