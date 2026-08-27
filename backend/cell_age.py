from __future__ import annotations

"""Cell biological-age estimation primitives.

An estimate is a model output with explicit uncertainty and provenance.  It is
not a claim of chronological age and must not be used as a diagnosis.
"""

from dataclasses import dataclass, field
from typing import Any

from .anatomy_foundation import CellObject, Evidence
from .data_foundation import Provenance, Uncertainty


@dataclass(frozen=True)
class CellAgeEstimate:
    estimate_id: str
    cell_id: str
    biological_age_years: float
    uncertainty: Uncertainty
    evidence: tuple[Evidence, ...]
    provenance: Provenance
    model_id: str
    model_version: str
    assessed_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.estimate_id.strip() or not self.cell_id.strip():
            raise ValueError("estimate_id and cell_id are required")
        if self.biological_age_years < 0:
            raise ValueError("biological age cannot be negative")
        if not self.evidence:
            raise ValueError("biological age estimate requires evidence")
        if not self.model_id.strip() or not self.model_version.strip():
            raise ValueError("biological age estimate requires model identity")
        self.uncertainty.validate()


def estimate_cell_age(*, estimate_id: str, cell: CellObject, biological_age_years: float, evidence: tuple[Evidence, ...], uncertainty: Uncertainty, provenance: Provenance, model_id: str, model_version: str, assessed_at: str, metadata: dict[str, Any] | None = None) -> CellAgeEstimate:
    cell.validate()
    estimate = CellAgeEstimate(estimate_id, cell.cell_id, biological_age_years, uncertainty, evidence, provenance, model_id, model_version, assessed_at, metadata or {})
    estimate.validate()
    return estimate
