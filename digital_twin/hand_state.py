"""Aggregate region states into a hand-level digital-twin state."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .region_state import RegionState


@dataclass(frozen=True)
class HandState:
    """Hand-level state preserving regional variation and traceability."""

    hand_id: str
    region_count: int
    region_ids: List[str]
    biological_age: Optional[float]
    biological_age_range: Optional[tuple[float, float]]
    confidence: float
    health_distribution: Dict[str, int]
    function_distribution: Dict[str, int]
    regional_heterogeneity: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hand_id": self.hand_id,
            "region_count": self.region_count,
            "region_ids": list(self.region_ids),
            "biological_age": self.biological_age,
            "biological_age_range": self.biological_age_range,
            "confidence": self.confidence,
            "health_distribution": dict(self.health_distribution),
            "function_distribution": dict(self.function_distribution),
            "regional_heterogeneity": self.regional_heterogeneity,
            "metadata": dict(self.metadata),
        }


def aggregate_hand_state(
    hand_id: str,
    regions: Iterable[RegionState],
    *,
    confidence: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> HandState:
    """Aggregate regions while retaining their identities and distributions."""
    region_list: List[RegionState] = list(regions)
    ages = [r.biological_age for r in region_list if r.biological_age is not None]
    health: Dict[str, int] = {}
    function: Dict[str, int] = {}
    for region in region_list:
        for status, count in region.health_distribution.items():
            health[status] = health.get(status, 0) + count
        for status, count in region.function_distribution.items():
            function[status] = function.get(status, 0) + count

    age = sum(ages) / len(ages) if ages else None
    age_range = (min(ages), max(ages)) if ages else None

    if region_list:
        mean_age = sum(r.biological_age for r in region_list if r.biological_age is not None) / len(ages) if ages else None
        age_spread = (
            sum(abs(r.biological_age - mean_age) for r in region_list if r.biological_age is not None) / len(ages)
            if mean_age is not None else 0.0
        )
        regional_heterogeneity = min(1.0, age_spread / 10.0)
        inferred_confidence = sum(r.confidence for r in region_list) / len(region_list)
    else:
        regional_heterogeneity = 0.0
        inferred_confidence = 0.0

    bounded = max(0.0, min(1.0, float(confidence if confidence is not None else inferred_confidence)))
    return HandState(
        hand_id=hand_id,
        region_count=len(region_list),
        region_ids=[r.region_id for r in region_list],
        biological_age=age,
        biological_age_range=age_range,
        confidence=bounded,
        health_distribution=health,
        function_distribution=function,
        regional_heterogeneity=regional_heterogeneity,
        metadata=metadata or {},
    )
