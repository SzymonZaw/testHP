from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CellState(str, Enum):
    HEALTHY = "healthy"
    ALTERED = "altered"
    STRESSED = "stressed"
    SENESCENT = "senescent"
    DAMAGED = "damaged"
    PATHOLOGICAL = "pathological"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CellHealthAssessment:
    cell_id: str
    state: CellState
    score: float | None = None
    confidence: float | None = None
    stress_signals: tuple[str, ...] = ()
    senescence_signals: tuple[str, ...] = ()
    damage_signals: tuple[str, ...] = ()
    morphology_flags: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    model_id: str | None = None
    model_version: str | None = None
    limitations: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.cell_id:
            raise ValueError("cell_id is required")
        for name, value in (("score", self.score), ("confidence", self.confidence)):
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.state is CellState.UNKNOWN and not self.limitations:
            raise ValueError("unknown state requires an explicit limitation")


@dataclass(frozen=True)
class CellHealthFeatureSet:
    cell_id: str
    features: dict[str, float] = field(default_factory=dict)
    source_ids: tuple[str, ...] = ()
    feature_version: str = "1"

    def validate(self) -> None:
        if not self.cell_id:
            raise ValueError("cell_id is required")
        if any(not isinstance(value, (int, float)) for value in self.features.values()):
            raise ValueError("cell health features must be numeric")
