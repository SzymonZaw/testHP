"""Observed biological trajectories derived from longitudinal observations."""
from __future__ import annotations

from dataclasses import dataclass

from .biological_timeline import BiologicalTimeline, ObservationChange


@dataclass(frozen=True)
class BiologicalTrajectory:
    """Describe an observed numeric trend without forecasting the future."""

    key: str
    changes: tuple[ObservationChange, ...]

    @classmethod
    def from_timeline(cls, timeline: BiologicalTimeline, key: str) -> "BiologicalTrajectory":
        return cls(key=key, changes=timeline.changes(key))

    @property
    def observation_count(self) -> int:
        return len(self.changes) + 1 if self.changes else 0

    @property
    def total_delta(self) -> float:
        return sum(change.delta for change in self.changes)

    @property
    def direction(self) -> str:
        if not self.changes:
            return "insufficient_data"
        if self.total_delta > 0:
            return "increasing"
        if self.total_delta < 0:
            return "decreasing"
        return "stable"

    @property
    def mean_delta(self) -> float | None:
        if not self.changes:
            return None
        return self.total_delta / len(self.changes)

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "observation_count": self.observation_count,
            "total_delta": self.total_delta,
            "mean_delta": self.mean_delta,
            "direction": self.direction,
            "changes": [change.__dict__ for change in self.changes],
        }
