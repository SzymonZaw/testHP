"""Longitudinal analysis of biological changes and trajectories."""

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Optional


@dataclass(frozen=True)
class LongitudinalPoint:
    timepoint_id: str
    timestamp: float
    value: float
    quality_score: float = 1.0


@dataclass(frozen=True)
class TrendResult:
    feature: str
    slope: Optional[float]
    direction: str
    baseline: Optional[float]
    latest: Optional[float]
    change: Optional[float]
    points_used: int
    insufficient_evidence: bool


class LongitudinalAnalyzer:
    """Estimate transparent trends; does not diagnose disease or aging."""

    def __init__(self, minimum_quality: float = 0.5, minimum_points: int = 2) -> None:
        if not 0 <= minimum_quality <= 1:
            raise ValueError("minimum_quality must be between 0 and 1")
        if minimum_points < 2:
            raise ValueError("minimum_points must be at least 2")
        self.minimum_quality = minimum_quality
        self.minimum_points = minimum_points

    def analyze(self, feature: str, points: Iterable[LongitudinalPoint]) -> TrendResult:
        valid = [
            point for point in points
            if point.quality_score >= self.minimum_quality
            and all(isfinite(value) for value in (point.timestamp, point.value, point.quality_score))
        ]
        valid.sort(key=lambda point: point.timestamp)

        if len(valid) < self.minimum_points:
            return TrendResult(feature, None, "insufficient_evidence", None, None, None, len(valid), True)

        x0 = valid[0].timestamp
        xs = [point.timestamp - x0 for point in valid]
        ys = [point.value for point in valid]
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        denominator = sum((x - mean_x) ** 2 for x in xs)
        if denominator == 0:
            return TrendResult(feature, None, "insufficient_evidence", ys[0], ys[-1], ys[-1] - ys[0], len(valid), True)

        slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator
        direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        return TrendResult(feature, slope, direction, ys[0], ys[-1], ys[-1] - ys[0], len(valid), False)
