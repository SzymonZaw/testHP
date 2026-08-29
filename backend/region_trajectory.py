"""Longitudinal analysis of anatomical-region state changes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .longitudinal_hand_twin import LongitudinalHandTwin


@dataclass(frozen=True)
class RegionTrajectoryPoint:
    observed_at: str
    biological_age: float | None
    cell_count: int
    confidence: float
    health_distribution: dict[str, int]
    function_distribution: dict[str, int]


@dataclass(frozen=True)
class RegionTrajectory:
    """Derived longitudinal changes for one anatomical region."""

    region_id: str
    points: tuple[RegionTrajectoryPoint, ...]

    @classmethod
    def from_twin(cls, twin: LongitudinalHandTwin, region_id: str) -> "RegionTrajectory":
        points: list[RegionTrajectoryPoint] = []
        for observation in twin.observations:
            region = observation.state.anatomical_regions.get(region_id)
            if region is None:
                continue
            points.append(
                RegionTrajectoryPoint(
                    observed_at=observation.observed_at,
                    biological_age=region.biological_age,
                    cell_count=region.cell_count,
                    confidence=region.confidence,
                    health_distribution=dict(region.health_distribution),
                    function_distribution=dict(region.function_distribution),
                )
            )
        return cls(region_id=region_id, points=tuple(points))

    @property
    def age_delta(self) -> float | None:
        ages = [point.biological_age for point in self.points if point.biological_age is not None]
        return ages[-1] - ages[0] if len(ages) >= 2 else None

    def ageing_rate(self) -> float | None:
        if len(self.points) < 2:
            return None
        first, last = self.points[0], self.points[-1]
        if first.biological_age is None or last.biological_age is None:
            return None
        start = datetime.fromisoformat(first.observed_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(last.observed_at.replace("Z", "+00:00"))
        years = (end - start).total_seconds() / (365.2425 * 24 * 3600)
        return (last.biological_age - first.biological_age) / years if years > 0 else None

    @property
    def cell_count_delta(self) -> int | None:
        if len(self.points) < 2:
            return None
        return self.points[-1].cell_count - self.points[0].cell_count

    @property
    def confidence_delta(self) -> float | None:
        if len(self.points) < 2:
            return None
        return self.points[-1].confidence - self.points[0].confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "points": [point.__dict__ for point in self.points],
            "age_delta": self.age_delta,
            "ageing_rate": self.ageing_rate(),
            "cell_count_delta": self.cell_count_delta,
            "confidence_delta": self.confidence_delta,
        }
