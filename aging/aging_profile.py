"""Aggregate aging signals by biological level."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .biological_clock import AgingClock, AgingClockResult, estimate_age


@dataclass(frozen=True)
class AgingProfile:
    """A transparent profile of aging-related scores, not a diagnosis."""

    scores: Mapping[str, AgingClockResult]

    @property
    def overall_score(self) -> float | None:
        if not self.scores:
            return None
        return sum(result.score for result in self.scores.values()) / len(self.scores)


def build_aging_profile(
    clocks: Mapping[str, AgingClock],
    features_by_level: Mapping[str, Mapping[str, float]],
) -> AgingProfile:
    """Run one clock per biological level and preserve missing-input information."""
    results: dict[str, AgingClockResult] = {}
    for level, clock in clocks.items():
        features = features_by_level.get(level, {})
        results[level] = estimate_age(clock, features)
    return AgingProfile(scores=results)
