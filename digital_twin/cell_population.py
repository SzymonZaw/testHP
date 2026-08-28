"""Aggregate single-cell states into explainable cell populations."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional

from .cell_state import CellState


@dataclass(frozen=True)
class CellPopulation:
    """Population-level view that preserves unknown measurements."""

    population_id: str
    cell_count: int
    health_distribution: Dict[str, int] = field(default_factory=dict)
    functional_distribution: Dict[str, int] = field(default_factory=dict)
    mean_biological_age: Optional[float] = None
    mean_functional_age: Optional[float] = None
    abnormal_fraction: Optional[float] = None
    senescent_fraction: Optional[float] = None
    mean_confidence: float = 0.0
    heterogeneity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "population_id": self.population_id,
            "cell_count": self.cell_count,
            "health_distribution": dict(self.health_distribution),
            "functional_distribution": dict(self.functional_distribution),
            "mean_biological_age": self.mean_biological_age,
            "mean_functional_age": self.mean_functional_age,
            "abnormal_fraction": self.abnormal_fraction,
            "senescent_fraction": self.senescent_fraction,
            "mean_confidence": self.mean_confidence,
            "heterogeneity": self.heterogeneity,
            "metadata": dict(self.metadata),
        }


def aggregate_cell_states(
    population_id: str,
    states: Iterable[CellState],
) -> CellPopulation:
    """Aggregate cells without treating unknown states as healthy."""
    cells = list(states)
    count = len(cells)
    if not count:
        return CellPopulation(population_id=population_id, cell_count=0)

    health = Counter(cell.health_state for cell in cells)
    function = Counter(cell.functional_state for cell in cells)
    biological_ages = [cell.biological_age for cell in cells if cell.biological_age is not None]
    functional_ages = [cell.functional_age for cell in cells if cell.functional_age is not None]
    confidences = [cell.confidence for cell in cells]

    abnormal = health.get("abnormal", 0) / count
    senescent = sum(
        1 for cell in cells
        if cell.senescent_cell_fraction is not None and cell.senescent_cell_fraction > 0.5
    ) / count

    # Heterogeneity is the share of cells not belonging to the most common
    # health state. It is descriptive, not a disease metric.
    dominant = max(health.values()) if health else 0
    heterogeneity = 1.0 - dominant / count

    return CellPopulation(
        population_id=population_id,
        cell_count=count,
        health_distribution=dict(sorted(health.items())),
        functional_distribution=dict(sorted(function.items())),
        mean_biological_age=mean(biological_ages) if biological_ages else None,
        mean_functional_age=mean(functional_ages) if functional_ages else None,
        abnormal_fraction=abnormal,
        senescent_fraction=senescent,
        mean_confidence=mean(confidences),
        heterogeneity=heterogeneity,
        metadata={"unknown_health_count": health.get("unknown", 0)},
    )
