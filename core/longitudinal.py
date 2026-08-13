"""Longitudinal comparison and trajectory utilities for BiologicalState."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .biological_state import BiologicalState


@dataclass(frozen=True)
class DimensionChange:
    name: str
    baseline: float
    current: float
    delta: float
    rate_per_day: float | None
    relative_change: float | None


@dataclass(frozen=True)
class LongitudinalComparison:
    subject_id: str
    baseline_timepoint: str
    current_timepoint: str
    elapsed_days: float
    changes: tuple[DimensionChange, ...]


def compare_states(
    baseline: BiologicalState,
    current: BiologicalState,
    elapsed_days: float,
) -> LongitudinalComparison:
    """Compare two states belonging to the same subject over a known interval."""
    if baseline.subject_id != current.subject_id:
        raise ValueError("States must belong to the same subject")
    if elapsed_days <= 0:
        raise ValueError("elapsed_days must be greater than zero")

    names = sorted(set(baseline.dimensions) | set(current.dimensions))
    changes: list[DimensionChange] = []
    for name in names:
        if name not in baseline.dimensions or name not in current.dimensions:
            continue
        old = baseline.dimensions[name]
        new = current.dimensions[name]
        delta = new - old
        rate = delta / elapsed_days
        relative = None if old == 0 else delta / abs(old)
        changes.append(DimensionChange(name, old, new, delta, rate, relative))

    return LongitudinalComparison(
        subject_id=baseline.subject_id,
        baseline_timepoint=baseline.timepoint_id,
        current_timepoint=current.timepoint_id,
        elapsed_days=float(elapsed_days),
        changes=tuple(changes),
    )


def trajectory(states: Sequence[BiologicalState], elapsed_days: Sequence[float]) -> dict[str, list[float]]:
    """Return ordered dimension values for a longitudinal series."""
    if len(states) != len(elapsed_days):
        raise ValueError("states and elapsed_days must have equal length")
    if not states:
        return {}
    subject_ids = {state.subject_id for state in states}
    if len(subject_ids) != 1:
        raise ValueError("All states must belong to the same subject")
    if any(day < 0 for day in elapsed_days):
        raise ValueError("elapsed_days cannot be negative")

    names = sorted({name for state in states for name in state.dimensions})
    return {
        name: [state.dimensions[name] for state in states if name in state.dimensions]
        for name in names
    }
