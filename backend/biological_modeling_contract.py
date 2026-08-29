from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgingTrajectory:
    subject_id: str
    cell_type: str | None
    horizons_years: tuple[int, ...] = (0, 5, 10, 20, 50)
    biological_age: dict[int, tuple[float, float]] | None = None
    aging_factors: tuple[str, ...] = ()
    uncertainty: dict[int, float] | None = None

    def validate(self) -> None:
        if not self.subject_id or not self.horizons_years:
            raise ValueError("aging trajectory identity and horizons are required")
        if tuple(sorted(self.horizons_years)) != self.horizons_years:
            raise ValueError("aging horizons must be ordered")
        if self.uncertainty:
            if any(h < 0 or u < 0 for h, u in self.uncertainty.items()):
                raise ValueError("aging uncertainty must be non-negative")


@dataclass(frozen=True)
class AgingModelRef:
    model_id: str
    model_version: str
    longitudinal_dataset_id: str | None = None
    personalized: bool = False


@dataclass(frozen=True)
class AgingModel:
    ref: AgingModelRef
    trajectories: tuple[AgingTrajectory, ...]
