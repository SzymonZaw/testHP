"""Longitudinal trajectory analysis for regions and tissues."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from .hand_observation import HandObservation


@dataclass(frozen=True)
class RegionalTrajectory:
    """Observed change for one region across hand observations."""

    structure_id: str
    structure_type: str
    points: List[Dict[str, Any]]
    direction: str
    age_change: Optional[float]
    age_slope_per_day: Optional[float]
    health_change: Dict[str, int]
    function_change: Dict[str, int]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "structure_id": self.structure_id,
            "structure_type": self.structure_type,
            "points": list(self.points),
            "direction": self.direction,
            "age_change": self.age_change,
            "age_slope_per_day": self.age_slope_per_day,
            "health_change": dict(self.health_change),
            "function_change": dict(self.function_change),
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


def _direction(change: Optional[float], tolerance: float) -> str:
    if change is None:
        return "insufficient"
    if abs(change) <= tolerance:
        return "stable"
    return "increasing" if change > 0 else "decreasing"


def _distribution_delta(first: Dict[str, int], last: Dict[str, int]) -> Dict[str, int]:
    keys = set(first) | set(last)
    return {key: last.get(key, 0) - first.get(key, 0) for key in sorted(keys) if last.get(key, 0) != first.get(key, 0)}


def _build_trajectory(
    structure_id: str,
    structure_type: str,
    points: List[Dict[str, Any]],
    tolerance: float,
) -> RegionalTrajectory:
    known = [p for p in points if p.get("biological_age") is not None]
    if len(known) < 2:
        confidence = sum(float(p.get("confidence", 0.0)) for p in points) / len(points) if points else 0.0
        return RegionalTrajectory(structure_id, structure_type, points, "insufficient", None, None, {}, {}, confidence)

    first, last = known[0], known[-1]
    change = float(last["biological_age"] - first["biological_age"])
    start = datetime.fromisoformat(first["observed_at"])
    end = datetime.fromisoformat(last["observed_at"])
    days = (end - start).total_seconds() / 86400.0
    slope = change / days if days > 0 else None
    confidence = sum(float(p.get("confidence", 0.0)) for p in known) / len(known)
    return RegionalTrajectory(
        structure_id,
        structure_type,
        points,
        _direction(change, tolerance),
        change,
        slope,
        _distribution_delta(first.get("health_distribution", {}), last.get("health_distribution", {})),
        _distribution_delta(first.get("function_distribution", {}), last.get("function_distribution", {})),
        confidence,
    )


def analyze_regional_trajectories(
    observations: Iterable[HandObservation],
    *,
    tolerance: float = 0.5,
) -> Dict[str, List[RegionalTrajectory]]:
    """Analyze region and tissue trajectories without clinical intervention claims."""
    ordered = sorted(observations, key=lambda item: item.observed_at)
    regions: Dict[str, List[Dict[str, Any]]] = {}
    tissues: Dict[str, List[Dict[str, Any]]] = {}

    for observation in ordered:
        for region_id, region in observation.regions.items():
            regions.setdefault(region_id, []).append({
                "observation_id": observation.observation_id,
                "observed_at": observation.observed_at,
                "biological_age": region.biological_age,
                "health_distribution": dict(region.health_distribution),
                "function_distribution": dict(region.function_distribution),
                "confidence": min(observation.confidence, region.confidence),
            })
        for tissue_id, tissue in observation.tissues.items():
            tissues.setdefault(tissue_id, []).append({
                "observation_id": observation.observation_id,
                "observed_at": observation.observed_at,
                "biological_age": tissue.biological_age,
                "health_distribution": dict(tissue.health_distribution),
                "function_distribution": dict(tissue.function_distribution),
                "confidence": min(observation.confidence, tissue.confidence),
            })

    return {
        "regions": [_build_trajectory(key, "region", value, tolerance) for key, value in regions.items()],
        "tissues": [_build_trajectory(key, "tissue", value, tolerance) for key, value in tissues.items()],
    }
