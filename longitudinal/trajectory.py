"""Transparent longitudinal trend analysis for biological measurements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class TrajectoryPoint:
    timepoint_id: str
    time: float
    values: Mapping[str, float]


@dataclass(frozen=True)
class Trend:
    feature: str
    slope: float
    intercept: float
    first_value: float
    last_value: float
    delta: float
    direction: str
    points: int


class TrajectoryAnalyzer:
    """Estimate simple linear trends without claiming clinical meaning."""

    def analyze(self, points: Iterable[TrajectoryPoint]) -> tuple[Trend, ...]:
        ordered = sorted(points, key=lambda point: point.time)
        if len(ordered) < 2:
            return ()
        features = sorted({name for point in ordered for name in point.values})
        trends: list[Trend] = []
        for feature in features:
            samples = [(p.time, p.values[feature]) for p in ordered if feature in p.values]
            if len(samples) < 2:
                continue
            slope, intercept = self._linear_fit(samples)
            first_value = samples[0][1]
            last_value = samples[-1][1]
            delta = last_value - first_value
            if slope > 0:
                direction = "increasing"
            elif slope < 0:
                direction = "decreasing"
            else:
                direction = "stable"
            trends.append(Trend(
                feature=feature,
                slope=slope,
                intercept=intercept,
                first_value=first_value,
                last_value=last_value,
                delta=delta,
                direction=direction,
                points=len(samples),
            ))
        return tuple(trends)

    @staticmethod
    def _linear_fit(samples: Sequence[tuple[float, float]]) -> tuple[float, float]:
        mean_x = sum(x for x, _ in samples) / len(samples)
        mean_y = sum(y for _, y in samples) / len(samples)
        denominator = sum((x - mean_x) ** 2 for x, _ in samples)
        if denominator == 0:
            return 0.0, mean_y
        slope = sum((x - mean_x) * (y - mean_y) for x, y in samples) / denominator
        return slope, mean_y - slope * mean_x
