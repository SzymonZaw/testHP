"""Aggregate cell inference trends through the hand hierarchy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional

from .cell_inference_history import InferenceTrend
from .spatial import HandSpatialModel


@dataclass
class HierarchicalInference:
    level: str
    identifier: str
    cells: int = 0
    health_counts: Dict[str, int] = field(default_factory=dict)
    aging_cells: int = 0
    abrupt_changes: int = 0
    mean_age: Optional[float] = None
    mean_confidence: Optional[float] = None
    hotspot_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "identifier": self.identifier,
            "cells": self.cells,
            "health_counts": dict(self.health_counts),
            "aging_cells": self.aging_cells,
            "abrupt_changes": self.abrupt_changes,
            "mean_age": self.mean_age,
            "mean_confidence": self.mean_confidence,
            "hotspot_score": self.hotspot_score,
        }


def _mean(values: Iterable[float]) -> Optional[float]:
    values = list(values)
    return sum(values) / len(values) if values else None


def aggregate_inference(
    model: HandSpatialModel,
    inferences: Dict[str, Any],
    trends: Optional[Dict[str, InferenceTrend]] = None,
) -> Dict[str, Dict[str, HierarchicalInference]]:
    """Aggregate latest cell inferences into tissue, region and hand summaries."""
    trends = trends or {}
    buckets: Dict[str, Dict[str, list[tuple[Any, Optional[InferenceTrend]]]]] = {"tissue": {}, "region": {}, "hand": {"hand": []}}
    for region in model.regions.values():
        buckets["region"].setdefault(region.region_id, [])
        for tissue in region.tissues.values():
            buckets["tissue"].setdefault(tissue.tissue_id, [])
            for cell in tissue.cells.values():
                inference = inferences.get(cell.cell_id)
                if inference is None:
                    continue
                item = (inference, trends.get(cell.cell_id))
                buckets["tissue"][tissue.tissue_id].append(item)
                buckets["region"][region.region_id].append(item)
                buckets["hand"]["hand"].append(item)

    result: Dict[str, Dict[str, HierarchicalInference]] = {}
    for level, groups in buckets.items():
        result[level] = {}
        for identifier, items in groups.items():
            health_counts: Dict[str, int] = {}
            ages, confidences = [], []
            aging = abrupt = 0
            for inference, trend in items:
                health_counts[inference.health_state] = health_counts.get(inference.health_state, 0) + 1
                if inference.biological_age is not None:
                    ages.append(float(inference.biological_age))
                confidences.append(float(inference.confidence))
                if trend and trend.direction == "aging":
                    aging += 1
                if trend and trend.abrupt_change:
                    abrupt += 1
            cells = len(items)
            abnormal = health_counts.get("abnormal_candidate", 0)
            hotspot_score = ((abnormal + aging + abrupt) / cells) if cells else 0.0
            result[level][identifier] = HierarchicalInference(
                level, identifier, cells, health_counts, aging, abrupt,
                _mean(ages), _mean(confidences), hotspot_score,
            )
    return result
