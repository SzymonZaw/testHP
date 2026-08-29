from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgingFactor:
    factor_id: str
    value: float
    unit: str | None = None
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgingTrajectoryPoint:
    target_time: str
    chronological_offset_years: float
    biological_age: float | None
    lower_bound: float | None = None
    upper_bound: float | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class AgingModel:
    model_id: str
    model_version: str
    reference_dataset_id: str | None
    factors: tuple[AgingFactor, ...]
    trajectory: tuple[AgingTrajectoryPoint, ...]
    tissue_scope: str = "unknown"
    cell_scope: str = "unknown"
    personalization_id: str | None = None
    longitudinal_dataset_id: str | None = None

    def validate(self) -> None:
        if not self.model_id or not self.model_version:
            raise ValueError("aging model identity is required")
        offsets = [p.chronological_offset_years for p in self.trajectory]
        if offsets != sorted(offsets):
            raise ValueError("aging trajectory must be chronological")
        for point in self.trajectory:
            if point.lower_bound is not None and point.upper_bound is not None and point.lower_bound > point.upper_bound:
                raise ValueError("aging uncertainty interval is invalid")
            if point.confidence is not None and not 0 <= point.confidence <= 1:
                raise ValueError("confidence must be between 0 and 1")
