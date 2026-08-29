from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class PathologySignal:
    signal_id: str
    spatial_id: str
    category: str
    severity: str = "unknown"
    score: float | None = None
    confidence: float | None = None
    cell_ids: tuple[str,...] = ()
    evidence_ids: tuple[str,...] = ()
    model_id: str | None = None
    model_version: str | None = None
    expert_validation_status: str = "unvalidated"
    limitations: tuple[str,...] = ()
    def validate(self)->None:
        for name,value in (("score",self.score),("confidence",self.confidence)):
            if value is not None and not 0<=value<=1: raise ValueError(f"{name} must be between 0 and 1")

@dataclass(frozen=True)
class AbnormalityCluster:
    cluster_id: str
    spatial_id: str
    signal_ids: tuple[str,...] = ()
    cell_ids: tuple[str,...] = ()
    tissue_ids: tuple[str,...] = ()
    confidence: float | None = None
    def validate(self)->None:
        if self.confidence is not None and not 0<=self.confidence<=1: raise ValueError("confidence must be between 0 and 1")
