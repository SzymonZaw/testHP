from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class AgingReference:
    reference_id: str
    cell_type: str
    dataset_id: str
    biomarker_names: tuple[str,...] = ()
    version: str = "1"

@dataclass(frozen=True)
class BiologicalAgeAssessment:
    cell_id: str
    cell_type: str
    chronological_age: float
    estimated_age: float
    lower_bound: float
    upper_bound: float
    confidence: float | None = None
    biomarkers: dict[str,float] = field(default_factory=dict)
    model_id: str | None = None
    model_version: str | None = None
    calibration_id: str | None = None
    validation_dataset_id: str | None = None
    validation_status: str = "unvalidated"
    uncertainty: float | None = None
    limitations: tuple[str,...] = ()
    def validate(self)->None:
        if self.lower_bound>self.estimated_age or self.estimated_age>self.upper_bound: raise ValueError("age estimate must lie inside interval")
        if self.confidence is not None and not 0<=self.confidence<=1: raise ValueError("confidence must be between 0 and 1")
        if self.uncertainty is not None and self.uncertainty<0: raise ValueError("uncertainty cannot be negative")
