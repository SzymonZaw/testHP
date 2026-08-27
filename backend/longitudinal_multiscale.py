from __future__ import annotations

"""Evidence-first aggregation of longitudinal cell trends into tissue/anatomy zones."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ZoneTrend:
    zone_id: str
    level: str
    metric: str
    cell_count: int
    changed_cells: int
    mean_delta: float | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "level": self.level,
            "metric": self.metric,
            "cell_count": self.cell_count,
            "changed_cells": self.changed_cells,
            "mean_delta": self.mean_delta,
            "status": self.status,
        }


def aggregate_cell_trends(
    trends: list[dict[str, Any]],
    *,
    cell_to_tissue: dict[str, str],
    tissue_to_anatomy: dict[str, str],
) -> list[dict[str, Any]]:
    """Aggregate already-observed cell trends upward without inventing missing data.

    Input trends must contain ``zone`` (cell id), ``metric`` and optional numeric
    ``delta``. A zone is marked ``attention`` when at least one observed cell
    changed; this is a research prioritisation signal, not a diagnosis or a
    treatment recommendation.
    """
    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for trend in trends:
        cell = str(trend.get("zone") or "")
        metric = str(trend.get("metric") or "unknown")
        if not cell or cell not in cell_to_tissue:
            continue
        tissue = cell_to_tissue[cell]
        anatomy = tissue_to_anatomy.get(tissue)
        if anatomy is None:
            continue
        for level, zone in (("tissue", tissue), ("anatomy", anatomy)):
            buckets.setdefault((level, zone, metric), []).append(trend)

    results: list[dict[str, Any]] = []
    for (level, zone, metric), items in sorted(buckets.items()):
        deltas = [float(x["delta"]) for x in items if isinstance(x.get("delta"), (int, float)) and not isinstance(x.get("delta"), bool)]
        changed = sum(1 for x in items if x.get("status") == "observed_change")
        mean_delta = round(sum(deltas) / len(deltas), 12) if deltas else None
        status = "attention" if changed else ("stable_observation" if items else "insufficient_data")
        results.append(ZoneTrend(zone, level, metric, len(items), changed, mean_delta, status).to_dict())
    return results
