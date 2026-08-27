from __future__ import annotations

"""Longitudinal aggregation for the multiscale hand digital twin.

This module compares already-derived observations across timepoints. It does
not diagnose disease, estimate lifespan, or prescribe treatment.
"""

from dataclasses import dataclass, asdict
from math import isfinite
from typing import Sequence


@dataclass(frozen=True)
class Trajectory:
    subject_id: str
    zone: str
    metric: str
    timepoints: tuple[str, ...]
    values: tuple[float, ...]
    delta: float | None
    relative_delta: float | None
    direction: str
    status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def summarize_trajectories(
    subject_id: str,
    observations: Sequence[dict[str, object]],
) -> list[Trajectory]:
    """Build deterministic trajectories from explicit numeric observations.

    Observations are grouped by ``zone``/``metric``. Boolean and non-finite
    values are ignored. Missing timepoints are never treated as normal.
    Duplicate zone/metric/timepoint observations are rejected because silently
    choosing one would hide an upstream data-quality problem.
    """
    if not subject_id.strip():
        raise ValueError("subject_id is required")

    groups: dict[tuple[str, str], dict[str, float]] = {}
    for observation in observations:
        zone = str(observation.get("zone") or observation.get("zone_id") or "unknown")
        metric = str(observation.get("metric") or "unknown")
        timepoint = str(observation.get("timepoint") or "").strip()
        value = observation.get("value")
        if not timepoint or isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        numeric = float(value)
        if not isfinite(numeric):
            continue
        bucket = groups.setdefault((zone, metric), {})
        if timepoint in bucket:
            raise ValueError(f"duplicate observation for {zone}/{metric}/{timepoint}")
        bucket[timepoint] = numeric

    results: list[Trajectory] = []
    for (zone, metric), bucket in sorted(groups.items()):
        ordered = sorted(bucket.items(), key=lambda item: item[0])
        timepoints = tuple(item[0] for item in ordered)
        values = tuple(item[1] for item in ordered)
        if len(values) < 2:
            delta = None
            relative_delta = None
            direction = "not_available"
            status = "insufficient_timepoints"
        else:
            delta = round(values[-1] - values[0], 12)
            relative_delta = None if values[0] == 0 else round(delta / abs(values[0]), 12)
            direction = "increased" if delta > 0 else "decreased" if delta < 0 else "stable"
            status = "observed_change" if delta != 0 else "stable_observation"
        results.append(Trajectory(
            subject_id=subject_id,
            zone=zone,
            metric=metric,
            timepoints=timepoints,
            values=values,
            delta=delta,
            relative_delta=relative_delta,
            direction=direction,
            status=status,
        ))
    return results
