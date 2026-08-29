from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PathologySeverity(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PathologySignal:
    signal_id: str
    spatial_id: str
    tissue_id: str | None = None
    cell_ids: tuple[str, ...] = ()
    category: str = "unknown"
    severity: PathologySeverity = PathologySeverity.UNKNOWN
    score: float | None = None
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()
    model_id: str | None = None
    model_version: str | None = None
    expert_validation_status: str = "not_validated"

    def validate(self) -> None:
        if not self.signal_id or not self.spatial_id:
            raise ValueError("signal_id and spatial_id are required")
        for name, value in (("score", self.score), ("confidence", self.confidence)):
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class AbnormalityCluster:
    cluster_id: str
    spatial_id: str
    signal_ids: tuple[str, ...]
    cell_ids: tuple[str, ...] = ()
    rationale: str = ""
    confidence: float | None = None

    def validate(self) -> None:
        if not self.cluster_id or not self.spatial_id or not self.signal_ids:
            raise ValueError("abnormality cluster requires identity, location and signals")
