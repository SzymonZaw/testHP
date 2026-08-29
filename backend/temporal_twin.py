from __future__ import annotations

"""Temporal digital-twin primitives: observations across explicit timepoints."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Timepoint:
    timepoint_id: str
    observed_at: str
    label: str | None = None


@dataclass(frozen=True)
class TemporalObservation:
    observation_id: str
    spatial_id: str
    timepoint_id: str
    state: dict[str, Any]
    evidence_ids: tuple[str, ...] = ()


def compare_observations(previous: TemporalObservation, current: TemporalObservation) -> dict[str, Any]:
    if previous.spatial_id != current.spatial_id:
        raise ValueError("temporal comparison requires the same spatial_id")
    return {
        "spatial_id": current.spatial_id,
        "from_timepoint": previous.timepoint_id,
        "to_timepoint": current.timepoint_id,
        "changed_keys": tuple(sorted(k for k in set(previous.state) | set(current.state)
                                     if previous.state.get(k) != current.state.get(k))),
    }
