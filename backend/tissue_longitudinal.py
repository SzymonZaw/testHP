from __future__ import annotations

"""Longitudinal tissue trajectories for the hand digital twin.

A trajectory links independently assessed tissue summaries across timepoints.
It reports trends; it does not diagnose disease or prescribe treatment.
"""

from dataclasses import dataclass, field
from typing import Any

from .data_foundation import Provenance, Uncertainty
from .tissue_intelligence import TissueStateSummary


@dataclass(frozen=True)
class TissueTrajectoryPoint:
    tissue_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    assessed_at: str
    dominant_state: str
    confidence: float
    cell_count: int
    state_fractions: dict[str, float]
    feature_means: dict[str, float] = field(default_factory=dict)
    source_summary_id: str = ""

    @classmethod
    def from_summary(cls, summary: TissueStateSummary, feature_means: dict[str, float] | None = None) -> "TissueTrajectoryPoint":
        summary.validate()
        return cls(summary.tissue_id, summary.subject_id, summary.hand_id, summary.timepoint_id,
                   summary.assessed_at, summary.dominant_state, summary.confidence,
                   summary.cell_count, dict(summary.state_fractions), dict(feature_means or {}), summary.summary_id)


@dataclass(frozen=True)
class TissueTrajectory:
    trajectory_id: str
    tissue_id: str
    subject_id: str
    hand_id: str
    points: tuple[TissueTrajectoryPoint, ...]
    provenance: Provenance
    uncertainty: Uncertainty

    def validate(self) -> None:
        if not self.trajectory_id.strip() or not self.tissue_id.strip():
            raise ValueError("trajectory_id and tissue_id are required")
        if not self.points:
            raise ValueError("tissue trajectory requires at least one point")
        for point in self.points:
            if (point.tissue_id, point.subject_id, point.hand_id) != (self.tissue_id, self.subject_id, self.hand_id):
                raise ValueError("trajectory points must share tissue/subject/hand")
            if not 0 <= point.confidence <= 1:
                raise ValueError("trajectory point confidence must be between 0 and 1")
            if point.cell_count <= 0:
                raise ValueError("trajectory point requires cells")
        self.uncertainty.validate()

    @property
    def timepoint_ids(self) -> tuple[str, ...]:
        return tuple(point.timepoint_id for point in self.points)

    def state_transitions(self) -> tuple[tuple[str, str, str], ...]:
        ordered = tuple(sorted(self.points, key=lambda point: point.assessed_at))
        return tuple((left.timepoint_id, left.dominant_state, right.dominant_state)
                     for left, right in zip(ordered, ordered[1:]) if left.dominant_state != right.dominant_state)

    def fraction_delta(self, state: str) -> float | None:
        if len(self.points) < 2:
            return None
        ordered = tuple(sorted(self.points, key=lambda point: point.assessed_at))
        return ordered[-1].state_fractions.get(state, 0.0) - ordered[0].state_fractions.get(state, 0.0)


def build_tissue_trajectory(summaries: tuple[TissueStateSummary, ...], *, trajectory_id: str) -> TissueTrajectory:
    if not summaries:
        raise ValueError("cannot build trajectory without tissue summaries")
    first = summaries[0]
    first.validate()
    if any((item.tissue_id, item.subject_id, item.hand_id) != (first.tissue_id, first.subject_id, first.hand_id) for item in summaries):
        raise ValueError("all summaries must refer to the same tissue/subject/hand")
    points = tuple(TissueTrajectoryPoint.from_summary(item) for item in summaries)
    points = tuple(sorted(points, key=lambda point: point.assessed_at))
    sources = tuple(point.source_summary_id for point in points if point.source_summary_id)
    trajectory = TissueTrajectory(
        trajectory_id=trajectory_id,
        tissue_id=first.tissue_id,
        subject_id=first.subject_id,
        hand_id=first.hand_id,
        points=points,
        provenance=Provenance(source_object_ids=sources, method="tissue-longitudinal-trajectory", method_version="1.0"),
        uncertainty=Uncertainty(kind="trajectory", score=sum(1.0 - point.confidence for point in points) / len(points)),
    )
    trajectory.validate()
    return trajectory
