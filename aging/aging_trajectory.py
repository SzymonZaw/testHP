"""Longitudinal analysis of biological-aging clock scores.

Scores are research signals only; they are not validated measures of human
biological age unless calibrated against an appropriate reference dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .biological_clock import AgingClockResult


@dataclass(frozen=True)
class AgingObservation:
    time: float
    result: AgingClockResult


@dataclass(frozen=True)
class AgingRate:
    clock_name: str
    slope: float
    delta: float
    direction: str
    observations: int


class AgingTrajectoryAnalyzer:
    """Estimate change in aging-clock scores across longitudinal observations."""

    def analyze(self, observations: Iterable[AgingObservation]) -> tuple[AgingRate, ...]:
        ordered = sorted(observations, key=lambda item: item.time)
        by_clock: dict[str, list[AgingObservation]] = {}
        for observation in ordered:
            by_clock.setdefault(observation.result.clock_name, []).append(observation)

        rates: list[AgingRate] = []
        for clock_name, samples in by_clock.items():
            if len(samples) < 2:
                continue
            first = samples[0]
            last = samples[-1]
            delta = last.result.score - first.result.score
            dt = last.time - first.time
            slope = delta / dt if dt != 0 else 0.0
            direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            rates.append(AgingRate(clock_name, slope, delta, direction, len(samples)))
        return tuple(rates)
