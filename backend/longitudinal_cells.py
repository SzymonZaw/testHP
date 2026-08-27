from __future__ import annotations

"""Longitudinal cell trajectories across repeated observations."""

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
        if not self.cell_id or not self.subject_id or not self.hand_id or not self.timepoint_id:
            raise ValueError("cell timepoint identity is required")
        if self.assessment is not None:
            self.assessment.validate()
        if self.biological_age is not None:
            self.biological_age.validate()


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


def build_cell_trajectory(records: list[CellTimepointRecord] | tuple[CellTimepointRecord, ...]) -> CellTrajectory:
    if not records:
        raise ValueError("at least one cell timepoint record is required")
    for record in records:
        record.validate()
    first = records[0]
    for record in records[1:]:
        if (record.cell_id, record.subject_id, record.hand_id) != (first.cell_id, first.subject_id, first.hand_id):
            raise ValueError("all trajectory records must share the same subject/hand/cell identity")
    timepoints = [record.timepoint_id for record in records]
    if len(timepoints) != len(set(timepoints)):
        raise ValueError("trajectory cannot contain duplicate timepoints")
    ordered = sorted(records, key=lambda record: record.timepoint_id)
    points = tuple(CellTrajectoryPoint(
        timepoint_id=record.timepoint_id,
        state=record.assessment.state if record.assessment else None,
        state_confidence=record.assessment.confidence if record.assessment else None,
        biological_age_years=record.biological_age.estimated_age_years if record.biological_age else None,
        age_interval=record.biological_age.uncertainty.interval if record.biological_age else None,
    ) for record in ordered)
    return CellTrajectory(first.cell_id, first.subject_id, first.hand_id, points)
