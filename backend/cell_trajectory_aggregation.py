from __future__ import annotations

"""Evidence-preserving aggregation of cell trajectories into tissue/anatomy trends."""

from dataclasses import dataclass
from typing import Any, Iterable

from .longitudinal_cells import CellTrajectory


@dataclass(frozen=True)
class AggregatedTrajectory:
    zone_id: str
    level: str
    metric: str
    cell_count: int
    changed_cells: int
    mean_delta: float | None
    status: str
    source_cell_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "level": self.level,
            "metric": self.metric,
            "cell_count": self.cell_count,
            "changed_cells": self.changed_cells,
            "mean_delta": self.mean_delta,
            "status": self.status,
            "source_cell_ids": self.source_cell_ids,
        }


def _age_delta(trajectory: CellTrajectory) -> float | None:
    return trajectory.biological_age_delta


def aggregate_cell_trajectories(
    trajectories: Iterable[CellTrajectory],
    *,
    cell_to_tissue: dict[str, str],
    tissue_to_anatomy: dict[str, str],
) -> list[AggregatedTrajectory]:
    """Roll biological-age trajectories from cells to tissue and anatomy.

    A changed cell is one with an observed age delta different from zero.
    Missing age observations are retained in the population count but do not
    contribute to the mean. Empty groups are not emitted.
    """
    grouped: dict[tuple[str, str], list[tuple[str, float | None]]] = {}
    for trajectory in trajectories:
        tissue = cell_to_tissue.get(trajectory.cell_id)
        if tissue is None:
            raise ValueError(f"missing tissue mapping for cell {trajectory.cell_id}")
        anatomy = tissue_to_anatomy.get(tissue)
        if anatomy is None:
            raise ValueError(f"missing anatomy mapping for tissue {tissue}")
        delta = _age_delta(trajectory)
        grouped.setdefault(("tissue", tissue), []).append((trajectory.cell_id, delta))
        grouped.setdefault(("anatomy", anatomy), []).append((trajectory.cell_id, delta))

    result: list[AggregatedTrajectory] = []
    for (level, zone_id), items in grouped.items():
        observed = [delta for _, delta in items if delta is not None]
        changed = [delta for delta in observed if delta != 0]
        mean = sum(observed) / len(observed) if observed else None
        status = "attention" if changed else ("stable_observation" if observed else "insufficient_observation")
        result.append(AggregatedTrajectory(zone_id, level, "biological_age_years", len(items), len(changed), mean, status, tuple(sorted(cell_id for cell_id, _ in items))))
    return sorted(result, key=lambda item: (0 if item.level == "anatomy" else 1, item.zone_id))
