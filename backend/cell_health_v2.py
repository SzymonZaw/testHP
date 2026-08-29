from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class CellState(str, Enum):
    HEALTHY="Healthy"; ALTERED="Altered"; STRESSED="Stressed"; SENESCENT="Senescent"; DAMAGED="Damaged"; UNKNOWN="Unknown"

@dataclass(frozen=True)
class HealthEvidence:
    evidence_id: str
    kind: str
    value: str
    source_id: str | None = None
    confidence: float | None = None

@dataclass(frozen=True)
class HealthBaseline:
    baseline_id: str
    cell_type: str
    feature_ranges: dict[str, tuple[float,float]] = field(default_factory=dict)
    reference_dataset_id: str | None = None
    version: str = "1"

@dataclass(frozen=True)
class CellHealthAssessment:
    cell_id: str
    state: CellState
    deviation_score: float | None = None
    stress_score: float | None = None
    senescence_score: float | None = None
    damage_score: float | None = None
    morphology_flags: tuple[str,...] = ()
    biomarkers: dict[str,float] = field(default_factory=dict)
    confidence: float | None = None
    evidence: tuple[HealthEvidence,...] = ()
    baseline_id: str | None = None
    expert_validation_status: str = "unvalidated"
    limitations: tuple[str,...] = ()
    def validate(self)->None:
        for name,value in (("deviation_score",self.deviation_score),("stress_score",self.stress_score),("senescence_score",self.senescence_score),("damage_score",self.damage_score),("confidence",self.confidence)):
            if value is not None and not 0<=value<=1: raise ValueError(f"{name} must be between 0 and 1")
        if self.state is CellState.UNKNOWN and not self.limitations: raise ValueError("Unknown assessment requires limitations")
