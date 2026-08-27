from __future__ import annotations

"""Longitudinal summaries for the hand digital twin.

This layer compares repeated observations. It reports trends and evidence
coverage, but deliberately does not turn a trend into a treatment decision.
"""

from dataclasses import dataclass
from typing import Sequence

from backend.biological_state import BiologicalAgeEstimate, BiologicalStateAssessment


@dataclass(frozen=True)
class TimepointBiologicalSummary:
    timepoint_id: str
    assessed_cell_count: int
    state_counts: dict[str, int]
    mean_confidence: float | None
    mean_biological_age_years: float | None


@dataclass(frozen=True)
class LongitudinalTrajectory:
    subject_id: str
    hand_id: str
    timepoints: tuple[TimepointBiologicalSummary, ...]
    biological_age_delta_years: float | None
    biological_age_trend: str
    state_transitions: tuple[str, ...]


def build_longitudinal_trajectory(
    subject_id: str,
    hand_id: str,
    assessments: Sequence[BiologicalStateAssessment],
    age_estimates: Sequence[BiologicalAgeEstimate] = (),
) -> LongitudinalTrajectory:
    """Build an evidence-preserving trajectory from repeated assessments.

    Inputs must belong to the requested subject/hand. ``biological_age_trend``
    is a descriptive trend only: ``increasing``, ``decreasing``, ``stable`` or
    ``insufficient_evidence``. State transitions are represented as
    ``timepoint:from->to`` only when a state's dominant label changes.
    """
    if not subject_id.strip() or not hand_id.strip():
        raise ValueError("subject_id and hand_id are required")

    for item in assessments:
        item.validate()
        if item.subject_id != subject_id or item.hand_id != hand_id:
            raise ValueError("assessment belongs to a different subject or hand")
    for item in age_estimates:
        item.validate()
        if item.subject_id != subject_id or item.hand_id != hand_id:
            raise ValueError("age estimate belongs to a different subject or hand")

    timepoint_ids = sorted(
        {item.timepoint_id for item in assessments} | {item.timepoint_id for item in age_estimates}
    )
    summaries: list[TimepointBiologicalSummary] = []
    dominant_states: list[tuple[str, str | None]] = []

    for timepoint_id in timepoint_ids:
        state_items = [item for item in assessments if item.timepoint_id == timepoint_id]
        age_items = [item for item in age_estimates if item.timepoint_id == timepoint_id]
        counts: dict[str, int] = {}
        confidences: list[float] = []
        for item in state_items:
            counts[item.state] = counts.get(item.state, 0) + 1
            if item.confidence is not None:
                confidences.append(item.confidence)
        ages = [item.estimated_age_years for item in age_items]
        mean_age = sum(ages) / len(ages) if ages else None
        dominant = max(counts, key=counts.get) if counts else None
        dominant_states.append((timepoint_id, dominant))
        summaries.append(
            TimepointBiologicalSummary(
                timepoint_id=timepoint_id,
                assessed_cell_count=len(state_items),
                state_counts=counts,
                mean_confidence=sum(confidences) / len(confidences) if confidences else None,
                mean_biological_age_years=mean_age,
            )
        )

    observed_ages = [item.mean_biological_age_years for item in summaries if item.mean_biological_age_years is not None]
    if len(observed_ages) >= 2:
        delta = observed_ages[-1] - observed_ages[0]
        if abs(delta) < 0.5:
            trend = "stable"
        elif delta > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
    else:
        delta = None
        trend = "insufficient_evidence"

    transitions: list[str] = []
    previous: str | None = None
    for timepoint_id, dominant in dominant_states:
        if previous is not None and dominant is not None and dominant != previous:
            transitions.append(f"{timepoint_id}:{previous}->{dominant}")
        if dominant is not None:
            previous = dominant

    return LongitudinalTrajectory(
        subject_id=subject_id,
        hand_id=hand_id,
        timepoints=tuple(summaries),
        biological_age_delta_years=delta,
        biological_age_trend=trend,
        state_transitions=tuple(transitions),
    )
