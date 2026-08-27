from __future__ import annotations

"""Temporal aggregation for multiscale hand observations.

The result is intentionally a decision-support signal: it describes observed
change and evidence coverage, rather than diagnosing disease or prescribing
intervention.
"""

from dataclasses import dataclass
from typing import Mapping, Sequence

from longitudinal.trajectory import TrajectoryAnalyzer, TrajectoryPoint, Trend


@dataclass(frozen=True)
class HandTrajectory:
    subject_id: str
    hand_id: str
    timepoints: tuple[str, ...]
    trends: tuple[Trend, ...]
    evidence_fraction: float
    signal: str


def analyze_hand_trajectory(
    subject_id: str,
    hand_id: str,
    observations: Sequence[tuple[str, float, Mapping[str, float]]],
    *,
    expected_timepoints: int | None = None,
) -> HandTrajectory:
    """Summarize longitudinal scalar signals for one hand.

    ``signal`` is one of ``insufficient_evidence``, ``stable_observation``, or
    ``changing_observation``. It deliberately does not encode a clinical
    recommendation.
    """
    if not subject_id.strip() or not hand_id.strip():
        raise ValueError("subject_id and hand_id are required")
    if expected_timepoints is not None and expected_timepoints < 1:
        raise ValueError("expected_timepoints must be positive")

    points = tuple(TrajectoryPoint(tp, time, values) for tp, time, values in observations)
    if len({point.timepoint_id for point in points}) != len(points):
        raise ValueError("timepoint_id values must be unique")

    trends = TrajectoryAnalyzer().analyze(points)
    expected = expected_timepoints if expected_timepoints is not None else len(points)
    evidence_fraction = min(1.0, len(points) / expected) if expected else 0.0

    if len(points) < 2 or not trends:
        signal = "insufficient_evidence"
    elif any(trend.direction != "stable" for trend in trends):
        signal = "changing_observation"
    else:
        signal = "stable_observation"

    ordered_ids = tuple(point.timepoint_id for point in sorted(points, key=lambda p: p.time))
    return HandTrajectory(
        subject_id=subject_id,
        hand_id=hand_id,
        timepoints=ordered_ids,
        trends=trends,
        evidence_fraction=evidence_fraction,
        signal=signal,
    )
