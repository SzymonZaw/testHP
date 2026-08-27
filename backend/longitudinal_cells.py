from __future__ import annotations

"""Longitudinal, evidence-first trajectories for cellular digital-twin data.

This module links already-assessed cell observations across timepoints. It does
not diagnose disease, infer treatment, or silently match unrelated cells.
Identity matching is explicit and context-bound; biological interpretation
remains the responsibility of validated upstream assessments.
"""

from dataclasses import dataclass, field
from typing import Any

from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment


@dataclass(frozen=True)
class CellTimepointRecord:
    cell_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    assessment: BiologicalStateAssessment | None = None
    biological_age: BiologicalAgeEstimate | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.cell_id.strip():
            raise ValueError("cell_id is required")
        if not self.subject_id.strip() or not self.hand_id.strip() or not self.timepoint_id.strip():
            raise ValueError("subject_id, hand_id and timepoint_id are required")
        if self.assessment is not None:
            self.assessment.validate()
            if self.assessment.target_object_id != self.cell_id:
                raise ValueError("assessment target must match cell_id")
            if (self.assessment.subject_id, self.assessment.hand_id, self.assessment.timepoint_id) != (
                self.subject_id, self.hand_id, self.timepoint_id
            ):
                raise ValueError("assessment context must match cell record")
        if self.biological_age is not None:
            self.biological_age.validate()
            if self.biological_age.target_object_id != self.cell_id:
                raise ValueError("biological age target must match cell_id")
            if (self.biological_age.subject_id, self.biological_age.hand_id, self.biological_age.timepoint_id) != (
                self.subject_id, self.hand_id, self.timepoint_id
            ):
                raise ValueError("biological age context must match cell record")


@dataclass(frozen=True)
class CellTrajectoryPoint:
    timepoint_id: str
    state: str | None
    state_confidence: float | None
    biological_age_years: float | None
    age_interval: tuple[float, float] | None


@dataclass(frozen=True)
class CellTrajectory:
    cell_id: str
    subject_id: str
    hand_id: str
    points: tuple[CellTrajectoryPoint, ...]

    @property
    def timepoint_count(self) -> int:
        return len(self.points)

    @property
    def state_sequence(self) -> tuple[str, ...]:
        return tuple(p.state for p in self.points if p.state is not None)

    @property
    def biological_age_delta(self) -> float | None:
        values = [p.biological_age_years for p in self.points if p.biological_age_years is not None]
        if len(values) < 2:
            return None
        return values[-1] - values[0]


def build_cell_trajectory(records: list[CellTimepointRecord] | tuple[CellTimepointRecord, ...]) -> CellTrajectory:
    """Build a deterministic trajectory for one cell across timepoints.

    Records must describe the same subject/hand/cell. Duplicate timepoints are
    rejected rather than silently overwritten. Ordering is lexical by
    ``timepoint_id`` because the domain model currently does not guarantee that
    IDs encode chronology; acquisition timestamps can be added later without
    changing the contract.
    """
    if not records:
        raise ValueError("at least one cell timepoint record is required")
    for record in records:
        record.validate()

    first = records[0]
    for record in records[1:]:
        if (record.cell_id, record.subject_id, record.hand_id) != (first.cell_id, first.subject_id, first.hand_id):
            raise ValueError("all trajectory records must share cell, subject and hand identity")

    timepoints = [record.timepoint_id for record in records]
    if len(timepoints) != len(set(timepoints)):
        raise ValueError("trajectory cannot contain duplicate timepoints")

    ordered = sorted(records, key=lambda record: record.timepoint_id)
    points = tuple(
        CellTrajectoryPoint(
            timepoint_id=record.timepoint_id,
            state=record.assessment.state if record.assessment else None,
            state_confidence=record.assessment.confidence if record.assessment else None,
            biological_age_years=record.biological_age.estimated_age_years if record.biological_age else None,
            age_interval=record.biological_age.uncertainty.interval if record.biological_age else None,
        )
        for record in ordered
    )
    return CellTrajectory(first.cell_id, first.subject_id, first.hand_id, points)


def trajectory_summary(trajectory: CellTrajectory) -> dict[str, Any]:
    """Return machine-readable longitudinal facts without clinical conclusions."""
    return {
        "cell_id": trajectory.cell_id,
        "subject_id": trajectory.subject_id,
        "hand_id": trajectory.hand_id,
        "timepoint_count": trajectory.timepoint_count,
        "timepoints": [p.timepoint_id for p in trajectory.points],
        "state_sequence": list(trajectory.state_sequence),
        "biological_age_delta_years": trajectory.biological_age_delta,
        "age_estimates": [
            {
                "timepoint_id": p.timepoint_id,
                "estimated_age_years": p.biological_age_years,
                "uncertainty_interval": p.age_interval,
            }
            for p in trajectory.points
            if p.biological_age_years is not None
        ],
        "interpretation": "longitudinal_observed_assessments_only",
    }
