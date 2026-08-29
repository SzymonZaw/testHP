from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BiologicalAgeAssessment:
    cell_id: str
    definition: str
    estimated_age: float | None
    chronological_age: float | None
    lower_bound: float | None = None
    upper_bound: float | None = None
    confidence: float | None = None
    biomarker_ids: tuple[str, ...] = ()
    reference_dataset_id: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    calibration_id: str | None = None
    validation_dataset_id: str | None = None
    limitations: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.cell_id or not self.definition:
            raise ValueError("cell_id and age definition are required")
        if self.estimated_age is None and not self.limitations:
            raise ValueError("missing biological age requires limitations")
        if self.lower_bound is not None and self.upper_bound is not None and self.lower_bound > self.upper_bound:
            raise ValueError("age interval is invalid")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
