from __future__ import annotations

"""Evidence-preserving aggregation of cell trajectories across hand scales."""

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
    confidence: float | None = None
    uncertainty_interval: tuple[float, float] | None = None
    evidence_ids: tuple[str, ...] = ()

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
            "confidence": self.confidence,
            "uncertainty_interval": self.uncertainty_interval,
            "evidence_ids": self.evidence_ids,
        }


def _age_delta(trajectory: CellTrajectory) -> float | None:
    return trajectory.biological_age_delta


def _confidence(trajectory: CellTrajectory) -> float | None:
    values = [point.state_confidence for point in trajectory.points if point.state_confidence is not None]
    identity = trajectory.identity_confidence
    if identity is not None:
        values.append(identity)
    return min(values) if values else None


def _uncertainty(trajectory: CellTrajectory) -> tuple[float, float] | None:
    intervals = [point.age_interval for point in trajectory.points if point.age_interval is not None]
    if not intervals:
        return None
    return (min(item[0] for item in intervals), max(item[1] for item in intervals))


def _evidence_ids(trajectory: CellTrajectory) -> tuple[str, ...]:
    return tuple(sorted({item.observation_id for item in trajectory.evidence if item.observation_id is not None}))


def _aggregate(grouped: dict[tuple[str, str], list[CellTrajectory]]) -> list[AggregatedTrajectory]:
    result: list[AggregatedTrajectory] = []
    for (level, zone_id), trajectories in grouped.items():
        deltas = [delta for trajectory in trajectories if (delta := _age_delta(trajectory)) is not None]
        changed = [delta for delta in deltas if delta != 0]
        mean = sum(deltas) / len(deltas) if deltas else None
        confidence_values = [value for trajectory in trajectories if (value := _confidence(trajectory)) is not None]
        confidence = min(confidence_values) if confidence_values else None
        intervals = [_uncertainty(trajectory) for trajectory in trajectories if _uncertainty(trajectory) is not None]
        uncertainty = (min(item[0] for item in intervals), max(item[1] for item in intervals)) if intervals else None
        evidence = tuple(sorted({evidence_id for trajectory in trajectories for evidence_id in _evidence_ids(trajectory)}))
        status = "attention" if changed else ("stable_observation" if deltas else "insufficient_observation")
        result.append(AggregatedTrajectory(
            zone_id=zone_id,
            level=level,
            metric="biological_age_years",
            cell_count=len(trajectories),
            changed_cells=len(changed),
            mean_delta=mean,
            status=status,
            source_cell_ids=tuple(sorted(trajectory.cell_id for trajectory in trajectories)),
            confidence=confidence,
            uncertainty_interval=uncertainty,
            evidence_ids=evidence,
        ))
    order = {"hand": 0, "anatomy": 1, "tissue": 2}
    return sorted(result, key=lambda item: (order.get(item.level, 99), item.zone_id))


def aggregate_cell_trajectories(
    trajectories: Iterable[CellTrajectory],
    *,
    cell_to_tissue: dict[str, str],
    tissue_to_anatomy: dict[str, str],
) -> list[AggregatedTrajectory]:
    """Roll biological-age trajectories from cells to tissue, anatomy and hand."""
    grouped: dict[tuple[str, str], list[CellTrajectory]] = {}
    for trajectory in trajectories:
        tissue = cell_to_tissue.get(trajectory.cell_id)
        if tissue is None:
            raise ValueError(f"missing tissue mapping for cell {trajectory.cell_id}")
        anatomy = tissue_to_anatomy.get(tissue)
        if anatomy is None:
            raise ValueError(f"missing anatomy mapping for tissue {tissue}")
        grouped.setdefault(("tissue", tissue), []).append(trajectory)
        grouped.setdefault(("anatomy", anatomy), []).append(trajectory)
        grouped.setdefault(("hand", trajectory.hand_id), []).append(trajectory)
    return _aggregate(grouped)
