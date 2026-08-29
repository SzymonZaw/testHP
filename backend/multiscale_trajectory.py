from __future__ import annotations

"""Longitudinal roll-up of cell states across the multiscale hand hierarchy."""

from dataclasses import dataclass
from typing import Iterable

from .longitudinal_cells import CellTrajectory


@dataclass(frozen=True)
class MultiscaleTrajectory:
    level: str
    node_id: str
    timepoint_count: int
    current_state: str | None
    previous_state: str | None
    state_change: str
    state_change_rate: float | None
    current_biological_age: float | None
    biological_age_delta: float | None
    confidence: float | None
    uncertainty_interval: tuple[float, float] | None
    evidence_ids: tuple[str, ...]
    source_cell_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "node_id": self.node_id,
            "timepoint_count": self.timepoint_count,
            "current_state": self.current_state,
            "previous_state": self.previous_state,
            "state_change": self.state_change,
            "state_change_rate": self.state_change_rate,
            "current_biological_age": self.current_biological_age,
            "biological_age_delta": self.biological_age_delta,
            "confidence": self.confidence,
            "uncertainty_interval": self.uncertainty_interval,
            "evidence_ids": self.evidence_ids,
            "source_cell_ids": self.source_cell_ids,
        }


def _state_from_counts(counts: dict[str, int]) -> str | None:
    if not counts:
        return None
    return max(counts, key=counts.get)


def _classify_change(previous: str | None, current: str | None) -> str:
    if previous is None or current is None:
        return "insufficient_observation"
    if previous == current:
        return "stable"
    if current == "diseased":
        return "worsening"
    if previous == "diseased" and current == "healthy":
        return "improving"
    return "state_transition"


def aggregate_health_trajectories(
    trajectories: Iterable[CellTrajectory],
    *,
    cell_to_population: dict[str, str],
    population_to_tissue: dict[str, str],
    tissue_to_region: dict[str, str],
    hand_id: str,
) -> list[MultiscaleTrajectory]:
    """Roll cell trajectories up to population, tissue, region and hand."""
    cells = list(trajectories)
    if not cells:
        return []

    grouped: dict[tuple[str, str], list[CellTrajectory]] = {}
    for trajectory in cells:
        population = cell_to_population.get(trajectory.cell_id)
        if population is None:
            raise ValueError(f"missing population mapping for cell {trajectory.cell_id}")
        tissue = population_to_tissue.get(population)
        if tissue is None:
            raise ValueError(f"missing tissue mapping for population {population}")
        region = tissue_to_region.get(tissue)
        if region is None:
            raise ValueError(f"missing region mapping for tissue {tissue}")
        for key in (("cell_population", population), ("tissue", tissue), ("region", region), ("hand", hand_id)):
            grouped.setdefault(key, []).append(trajectory)

    result: list[MultiscaleTrajectory] = []
    for (level, node_id), members in grouped.items():
        max_points = max(len(item.points) for item in members)
        current_points = [item.points[-1] for item in members if item.points]
        previous_points = [item.points[-2] for item in members if len(item.points) >= 2]
        current_counts: dict[str, int] = {}
        previous_counts: dict[str, int] = {}
        for point in current_points:
            if point.state is not None:
                current_counts[point.state] = current_counts.get(point.state, 0) + 1
        for point in previous_points:
            if point.state is not None:
                previous_counts[point.state] = previous_counts.get(point.state, 0) + 1
        current = _state_from_counts(current_counts)
        previous = _state_from_counts(previous_counts)
        change = _classify_change(previous, current)
        confidence_values = [p.state_confidence for p in current_points if p.state_confidence is not None]
        ages = [p.biological_age_years for p in current_points if p.biological_age_years is not None]
        deltas = [item.biological_age_delta for item in members if item.biological_age_delta is not None]
        intervals = [p.age_interval for p in current_points if p.age_interval is not None]
        evidence_ids = tuple(sorted({e.evidence_id for item in members for e in item.evidence if e.evidence_id}))
        result.append(MultiscaleTrajectory(
            level=level,
            node_id=node_id,
            timepoint_count=max_points,
            current_state=current,
            previous_state=previous,
            state_change=change,
            state_change_rate=(sum(1 for a, b in zip(previous_points, current_points) if a.state != b.state) / len(members)) if previous_points else None,
            current_biological_age=sum(ages) / len(ages) if ages else None,
            biological_age_delta=sum(deltas) / len(deltas) if deltas else None,
            confidence=min(confidence_values) if confidence_values else None,
            uncertainty_interval=(min(i[0] for i in intervals), max(i[1] for i in intervals)) if intervals else None,
            evidence_ids=evidence_ids,
            source_cell_ids=tuple(sorted(item.cell_id for item in members)),
        ))
    order = {"cell_population": 0, "tissue": 1, "region": 2, "hand": 3}
    return sorted(result, key=lambda item: (order[item.level], item.node_id))
