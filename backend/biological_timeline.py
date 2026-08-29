"""Time-series utilities for biological observations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .biological_hierarchy import BiologicalObservation


@dataclass(frozen=True)
class ObservationChange:
    """Observed change between two measurements of the same value."""

    key: str
    previous: float
    current: float
    delta: float
    direction: str
    previous_timestamp: str
    current_timestamp: str


@dataclass(frozen=True)
class BiologicalTimeline:
    """Chronologically ordered observations without inferred measurements."""

    observations: tuple[BiologicalObservation, ...] = ()

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.observations, key=lambda item: datetime.fromisoformat(item.timestamp.replace("Z", "+00:00"))))
        if ordered != self.observations:
            object.__setattr__(self, "observations", ordered)

    def add(self, observation: BiologicalObservation) -> "BiologicalTimeline":
        return BiologicalTimeline(self.observations + (observation,))

    def changes(self, key: str) -> tuple[ObservationChange, ...]:
        points: list[tuple[BiologicalObservation, float]] = []
        for observation in self.observations:
            value: Any = observation.values.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                points.append((observation, float(value)))
        changes: list[ObservationChange] = []
        for (previous_observation, previous), (current_observation, current) in zip(points, points[1:]):
            delta = current - previous
            direction = "increasing" if delta > 0 else "decreasing" if delta < 0 else "stable"
            changes.append(ObservationChange(key, previous, current, delta, direction, previous_observation.timestamp, current_observation.timestamp))
        return tuple(changes)

    def latest(self) -> BiologicalObservation | None:
        return self.observations[-1] if self.observations else None
