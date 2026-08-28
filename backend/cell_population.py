from __future__ import annotations

"""Aggregated state of a cell population with traceable source cells."""

from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any, Iterable

from .longitudinal_cells import CellTrajectory


@dataclass(frozen=True)
class CellPopulation:
    population_id: str
    cell_type: str | None
    cell_count: int
    source_cell_ids: tuple[str, ...]
    biological_age_mean: float | None = None
    biological_age_min: float | None = None
    biological_age_max: float | None = None
    healthy_fraction: float | None = None
    abnormal_fraction: float | None = None
    senescent_fraction: float | None = None
    proliferating_fraction: float | None = None
    function_score_mean: float | None = None
    confidence: float = 0.0
    evidence: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    health_distribution: dict[str, int] = field(default_factory=dict)
    functional_distribution: dict[str, int] = field(default_factory=dict)

    @property
    def mean_biological_age(self) -> float | None:
        return self.biological_age_mean

    @property
    def mean_confidence(self) -> float:
        return self.confidence

    @property
    def heterogeneity(self) -> float:
        if self.cell_count <= 1:
            return 0.0
        dominant = max(self.health_distribution.values(), default=0)
        return 1.0 - dominant / self.cell_count

    def validate(self) -> None:
        if not self.population_id:
            raise ValueError("population_id is required")
        if self.cell_count < 0:
            raise ValueError("cell_count cannot be negative")
        if self.cell_count != len(self.source_cell_ids):
            raise ValueError("cell_count must match source_cell_ids")
        if len(set(self.source_cell_ids)) != len(self.source_cell_ids):
            raise ValueError("source_cell_ids must be unique")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("population confidence must be between 0 and 1")
        for name in ("healthy_fraction", "abnormal_fraction", "senescent_fraction", "proliferating_fraction"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        for distribution_name in ("health_distribution", "functional_distribution"):
            distribution = getattr(self, distribution_name)
            if any(count < 0 for count in distribution.values()):
                raise ValueError(f"{distribution_name} cannot contain negative counts")
            if distribution and sum(distribution.values()) != self.cell_count:
                raise ValueError(f"{distribution_name} must sum to cell_count")
        if self.biological_age_min is not None and self.biological_age_max is not None:
            if self.biological_age_min > self.biological_age_max:
                raise ValueError("biological age minimum cannot exceed maximum")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def build_cell_population(
    population_id: str,
    trajectories: Iterable[CellTrajectory],
    *,
    cell_type: str | None = None,
) -> CellPopulation:
    """Aggregate latest cell-level state while preserving provenance."""
    items = tuple(trajectories)
    if not items:
        raise ValueError("at least one trajectory is required")

    source_ids = tuple(sorted(trajectory.cell_id for trajectory in items))
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("trajectories must contain unique cell ids")

    latest_points = tuple(
        trajectory.points[-1]
        for trajectory in items
        if trajectory.points
    )
    ages = [point.biological_age_years for point in latest_points if point.biological_age_years is not None]
    states = [point.state for point in latest_points if point.state is not None]
    state_counts: dict[str, int] = {}
    for state in states:
        state_counts[state] = state_counts.get(state, 0) + 1

    abnormal_states = {"abnormal", "deteriorating", "diseased"}
    healthy_count = state_counts.get("healthy", 0)
    abnormal_count = sum(state_counts.get(state, 0) for state in abnormal_states)
    senescent_count = state_counts.get("senescent", 0)
    confidence_values = [point.state_confidence for point in latest_points if point.state_confidence is not None]

    evidence = tuple(
        {
            "source": "cell_trajectory",
            "cell_id": trajectory.cell_id,
            "identity_quality": trajectory.assess_identity_quality(),
        }
        for trajectory in items
    )

    population = CellPopulation(
        population_id=population_id,
        cell_type=cell_type,
        cell_count=len(source_ids),
        source_cell_ids=source_ids,
        biological_age_mean=mean(ages) if ages else None,
        biological_age_min=min(ages) if ages else None,
        biological_age_max=max(ages) if ages else None,
        healthy_fraction=healthy_count / len(states) if states else None,
        abnormal_fraction=abnormal_count / len(states) if states else None,
        senescent_fraction=senescent_count / len(states) if states else None,
        confidence=min(confidence_values) if confidence_values else 0.0,
        evidence=evidence,
        health_distribution=state_counts,
    )
    population.validate()
    return population
