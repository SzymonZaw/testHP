"""Hierarchical aggregation of cell assessments.

The module summarizes evidence-aware cell assessments at tissue, region, and
hand levels without turning summaries into clinical recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional

from .cell_assessment import CellAssessment
from .spatial import HandSpatialModel


@dataclass
class LevelAssessment:
    level: str
    identifier: str
    assessed_cells: int = 0
    health_score_mean: Optional[float] = None
    abnormality_mean: Optional[float] = None
    biological_age_mean: Optional[float] = None
    uncertainty_mean: Optional[float] = None
    state_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "identifier": self.identifier,
            "assessed_cells": self.assessed_cells,
            "health_score_mean": self.health_score_mean,
            "abnormality_mean": self.abnormality_mean,
            "biological_age_mean": self.biological_age_mean,
            "uncertainty_mean": self.uncertainty_mean,
            "state_counts": dict(self.state_counts),
        }


def _mean(values: Iterable[Optional[float]]) -> Optional[float]:
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    return sum(numeric) / len(numeric) if numeric else None


def aggregate_assessments(
    model: HandSpatialModel,
    assessments: Dict[str, CellAssessment],
) -> Dict[str, Dict[str, LevelAssessment]]:
    """Aggregate latest cell assessments through the spatial hierarchy."""
    buckets: Dict[str, Dict[str, list[CellAssessment]]] = {
        "tissue": {},
        "region": {},
        "hand": {"hand": []},
    }

    for region in model.regions.values():
        buckets["region"].setdefault(region.region_id, [])
        for tissue in region.tissues.values():
            buckets["tissue"].setdefault(tissue.tissue_id, [])
            for cell in tissue.cells.values():
                assessment = assessments.get(cell.cell_id)
                if assessment is None:
                    continue
                buckets["tissue"][tissue.tissue_id].append(assessment)
                buckets["region"][region.region_id].append(assessment)
                buckets["hand"]["hand"].append(assessment)

    result: Dict[str, Dict[str, LevelAssessment]] = {}
    for level, groups in buckets.items():
        result[level] = {}
        for identifier, items in groups.items():
            state_counts: Dict[str, int] = {}
            for item in items:
                state_counts[item.health_state] = state_counts.get(item.health_state, 0) + 1
            result[level][identifier] = LevelAssessment(
                level=level,
                identifier=identifier,
                assessed_cells=len(items),
                health_score_mean=_mean(item.health_score for item in items),
                abnormality_mean=_mean(item.abnormality_score for item in items),
                biological_age_mean=_mean(item.biological_age for item in items),
                uncertainty_mean=_mean(item.uncertainty for item in items),
                state_counts=state_counts,
            )
    return result
