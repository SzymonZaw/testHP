from __future__ import annotations

"""Temporal aggregation for multiscale hand observations.

The result is intentionally a decision-support signal: it describes observed
change and evidence coverage, rather than diagnosing disease or prescribing
intervention.
"""

from dataclasses import dataclass
from datetime import datetime
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


def analyze_longitudinal_twin(
    twin: "LongitudinalHandTwin",
    *,
    subject_id: str | None = None,
    expected_timepoints: int | None = None,
) -> HandTrajectory:
    """Adapt a ``LongitudinalHandTwin`` into the existing trajectory analyzer.

    Calendar time is converted to fractional years relative to the first
    observation so the shared trajectory engine can compare measurements made
    at different dates.
    """
    from backend.longitudinal_hand_twin import LongitudinalHandTwin

    if not isinstance(twin, LongitudinalHandTwin):
        raise TypeError("twin must be a LongitudinalHandTwin")

    if not twin.observations:
        return analyze_hand_trajectory(
            subject_id or str(twin.metadata.get("subject_id", twin.hand_id)),
            twin.hand_id,
            (),
            expected_timepoints=expected_timepoints,
        )

    parsed = [datetime.fromisoformat(item.observed_at.replace("Z", "+00:00")) for item in twin.observations]
    origin = parsed[0]
    observations = []
    for observation, timestamp in zip(twin.observations, parsed):
        state = observation.state
        values: dict[str, float] = {
            "cell_count": float(state.cell_count),
            "confidence": float(state.confidence),
        }
        if state.biological_age is not None:
            values["biological_age"] = float(state.biological_age)
        elapsed_years = (timestamp - origin).total_seconds() / (365.2425 * 24 * 3600)
        observations.append((observation.observed_at, elapsed_years, values))

    return analyze_hand_trajectory(
        subject_id or str(twin.metadata.get("subject_id", twin.hand_id)),
        twin.hand_id,
        observations,
        expected_timepoints=expected_timepoints,
    )
