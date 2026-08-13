"""Simple, interpretable biological-age clock primitives.

This module deliberately does not claim to estimate real human biological age.
It provides a transparent scoring layer that can later be calibrated against
validated longitudinal datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence


@dataclass(frozen=True)
class AgingClock:
    """Weighted linear clock over normalized biological features."""

    name: str
    weights: Mapping[str, float]
    intercept: float = 0.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Clock name cannot be empty")
        if not self.weights:
            raise ValueError("Clock requires at least one feature")
        if not all(isfinite(float(weight)) for weight in self.weights.values()):
            raise ValueError("Clock weights must be finite")

    def predict(self, features: Mapping[str, float]) -> float:
        return float(
            self.intercept
            + sum(float(self.weights[name]) * float(features.get(name, 0.0)) for name in self.weights)
        )


@dataclass(frozen=True)
class AgingClockResult:
    clock_name: str
    score: float
    contributing_features: tuple[str, ...]
    missing_features: tuple[str, ...]


def estimate_age(clock: AgingClock, features: Mapping[str, float]) -> AgingClockResult:
    """Produce a transparent clock score and report missing inputs."""
    missing = tuple(name for name in clock.weights if name not in features)
    score = clock.predict(features)
    return AgingClockResult(
        clock_name=clock.name,
        score=score,
        contributing_features=tuple(clock.weights),
        missing_features=missing,
    )


def z_score(value: float, mean: float, std: float) -> float:
    """Normalize a biomarker using a reference population."""
    if not isfinite(float(std)) or std <= 0:
        raise ValueError("Reference standard deviation must be greater than zero")
    return (float(value) - float(mean)) / float(std)
