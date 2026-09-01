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


class CellAction(str, Enum):
    NO_ACTION = "no_action"
    MONITOR = "monitor"
    INVESTIGATE = "investigate"
    INTERVENE = "intervene"


@dataclass(frozen=True)
class CellHealthAssessment:
    """Interpretation envelope; it never turns missing evidence into a claim."""

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
    action: CellAction = CellAction.NO_ACTION

    def validate(self) -> None:
        if not self.cell_id:
            raise ValueError("cell_id is required")
        for name, value in (("score", self.score), ("confidence", self.confidence)):
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.state is CellState.UNKNOWN and not self.limitations:
            raise ValueError("unknown state requires an explicit limitation")
        if self.state is CellState.HEALTHY and self.model_id is None and not self.evidence_ids:
            raise ValueError("healthy state requires evidence or a model identifier")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "cell_id": self.cell_id,
            "state": self.state.value,
            "score": self.score,
            "confidence": self.confidence,
            "stress_signals": self.stress_signals,
            "senescence_signals": self.senescence_signals,
            "damage_signals": self.damage_signals,
            "morphology_flags": self.morphology_flags,
            "evidence_ids": self.evidence_ids,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "limitations": self.limitations,
            "action": self.action.value,
        }


@dataclass(frozen=True)
class CellBiologicalAge:
    """Optional model-derived biological age; None means not assessed."""

    cell_id: str
    biological_age_years: float | None = None
    chronological_age_years: float | None = None
    age_deviation_years: float | None = None
    lower_bound_years: float | None = None
    upper_bound_years: float | None = None
    confidence: float | None = None
    model_id: str | None = None
    model_version: str | None = None
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.cell_id:
            raise ValueError("cell_id is required")
        for name, value in (
            ("biological_age_years", self.biological_age_years),
            ("chronological_age_years", self.chronological_age_years),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.lower_bound_years is not None and self.upper_bound_years is not None:
            if self.lower_bound_years > self.upper_bound_years:
                raise ValueError("age uncertainty interval is invalid")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.biological_age_years is not None and self.model_id is None:
            raise ValueError("model_id is required for a biological-age estimate")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "cell_id": self.cell_id,
            "biological_age_years": self.biological_age_years,
            "chronological_age_years": self.chronological_age_years,
            "age_deviation_years": self.age_deviation_years,
            "lower_bound_years": self.lower_bound_years,
            "upper_bound_years": self.upper_bound_years,
            "confidence": self.confidence,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "evidence_ids": self.evidence_ids,
            "limitations": self.limitations,
            "claim_status": "model_derived" if self.biological_age_years is not None else "not_assessed",
        }


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

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "cell_id": self.cell_id,
            "features": dict(self.features),
            "source_ids": self.source_ids,
            "feature_version": self.feature_version,
        }
