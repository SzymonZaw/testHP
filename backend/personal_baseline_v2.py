from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class BaselineFeature:
    name: str
    unit: str
    center: float
    lower: float
    upper: float
    variability: float | None = None

@dataclass(frozen=True)
class PersonalBaseline:
    baseline_id: str
    subject_id: str
    features: tuple[BaselineFeature,...] = ()
    source_timepoint_ids: tuple[str,...] = ()
    population_reference_id: str | None = None
    version: str = "1"

@dataclass(frozen=True)
class BaselineDeviation:
    subject_id: str
    baseline_id: str
    current_timepoint_id: str
    deviations: dict[str,float] = field(default_factory=dict)
    comparison: str = "personal-first"
    population_comparison_used: bool = False
    confidence: float | None = None
    def validate(self)->None:
        if self.confidence is not None and not 0<=self.confidence<=1: raise ValueError("confidence must be between 0 and 1")
