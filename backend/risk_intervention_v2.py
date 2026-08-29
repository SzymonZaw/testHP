from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class RiskLevel(str, Enum):
    NORMAL="normal"; MONITOR="monitor"; ELEVATED="elevated"; HIGH="high"; UNKNOWN="unknown"

@dataclass(frozen=True)
class RiskMapEntry:
    spatial_id: str
    level: RiskLevel
    score: float | None = None
    confidence: float | None = None
    evidence_ids: tuple[str,...] = ()
    rationale: str = ""
    model_id: str | None = None
    model_version: str | None = None
    def validate(self)->None:
        for name,value in (("score",self.score),("confidence",self.confidence)):
            if value is not None and not 0<=value<=1: raise ValueError(f"{name} must be between 0 and 1")

class InterventionAction(str, Enum):
    OBSERVE="observe"; INVESTIGATE="investigate"; TREAT="treat"; REGENERATE="regenerate"; NONE="none"

@dataclass(frozen=True)
class InterventionMapEntry:
    spatial_id: str
    action: InterventionAction
    priority: int = 0
    confidence: float | None = None
    evidence_ids: tuple[str,...] = ()
    rationale: str = ""
    limitations: tuple[str,...] = ()
    expert_review_status: str = "required"
    def validate(self)->None:
        if self.priority<0: raise ValueError("priority cannot be negative")
        if self.confidence is not None and not 0<=self.confidence<=1: raise ValueError("confidence must be between 0 and 1")
        if self.action in {InterventionAction.TREAT,InterventionAction.REGENERATE} and self.expert_review_status=="not_required": raise ValueError("clinical actions require expert review")
