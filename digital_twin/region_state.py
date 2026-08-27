"""Aggregate tissue states into a region-level digital-twin state."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .tissue_state import TissueState


@dataclass(frozen=True)
class RegionState:
    """Region-level state that preserves tissue-level variation."""

    region_id: str
    tissue_count: int
    tissue_ids: List[str]
    biological_age: Optional[float]
    biological_age_range: Optional[tuple[float, float]]
    confidence: float
    health_distribution: Dict[str, int]
    function_distribution: Dict[str, int]
    heterogeneity: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "tissue_count": self.tissue_count,
            "tissue_ids": list(self.tissue_ids),
            "biological_age": self.biological_age,
            "biological_age_range": self.biological_age_range,
            "confidence": self.confidence,
            "health_distribution": dict(self.health_distribution),
            "function_distribution": dict(self.function_distribution),
            "heterogeneity": self.heterogeneity,
            "metadata": dict(self.metadata),
        }


def aggregate_region_state(
    region_id: str,
    tissues: Iterable[TissueState],
    *,
    confidence: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> RegionState:
    """Aggregate tissues without collapsing their individual distributions."""
    tissue_list: List[TissueState] = list(tissues)
    ages = [t.biological_age for t in tissue_list if t.biological_age is not None]
    health: Dict[str, int] = {}
    function: Dict[str, int] = {}
    for tissue in tissue_list:
        for status, count in tissue.health_distribution.items():
            health[status] = health.get(status, 0) + count
        for status, count in tissue.function_distribution.items():
            function[status] = function.get(status, 0) + count

    if ages:
        age = sum(ages) / len(ages)
        age_range = (min(ages), max(ages))
    else:
        age = None
        age_range = None

    total = sum(health.values())
    heterogeneity = 1.0 - max(health.values()) / total if total else 0.0
    inferred_confidence = (
        sum(t.confidence for t in tissue_list) / len(tissue_list)
        if tissue_list else 0.0
    )
    bounded = max(0.0, min(1.0, float(confidence if confidence is not None else inferred_confidence)))

    return RegionState(
        region_id=region_id,
        tissue_count=len(tissue_list),
        tissue_ids=[t.tissue_type for t in tissue_list],
        biological_age=age,
        biological_age_range=age_range,
        confidence=bounded,
        health_distribution=health,
        function_distribution=function,
        heterogeneity=heterogeneity,
        metadata=metadata or {},
    )
