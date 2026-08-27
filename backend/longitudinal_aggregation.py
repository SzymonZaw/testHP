from __future__ import annotations

"""Longitudinal aggregation for the multiscale hand digital twin.

Aggregates already-derived cell assessments without inventing diagnoses or
silently filling missing observations. Every aggregate retains coverage and
uncertainty so downstream UI/model layers can distinguish evidence from gaps.
"""

from dataclasses import dataclass, field
from typing import Iterable

from .anatomy_foundation import CellObject, TissueRegion
from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment


@dataclass(frozen=True)
class CellLongitudinalPoint:
    cell_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    state: str | None = None
    state_confidence: float | None = None
    biological_age_years: float | None = None
    biological_age_interval: tuple[float, float] | None = None


@dataclass(frozen=True)
class TissueLongitudinalState:
    tissue_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    cell_count: int
    assessed_cell_count: int
    state_counts: dict[str, int]
    state_coverage: float
    mean_biological_age_years: float | None
    biological_age_interval: tuple[float, float] | None

    def validate(self) -> None:
        if self.cell_count < 0 or self.assessed_cell_count < 0:
            raise ValueError("cell counts cannot be negative")
        if self.assessed_cell_count > self.cell_count:
            raise ValueError("assessed cells cannot exceed total cells")
        if not 0 <= self.state_coverage <= 1:
            raise ValueError("state coverage must be between 0 and 1")
        if self.biological_age_interval is not None and self.biological_age_interval[0] > self.biological_age_interval[1]:
            raise ValueError("biological age interval is invalid")


@dataclass(frozen=True)
class HandLongitudinalState:
    subject_id: str
    hand_id: str
    timepoint_id: str
    tissue_count: int
    tissues_with_cell_assessments: int
    tissue_states: tuple[TissueLongitudinalState, ...] = field(default_factory=tuple)
    coverage: float = 0.0

    def validate(self) -> None:
        if self.tissue_count < 0 or self.tissues_with_cell_assessments < 0:
            raise ValueError("tissue counts cannot be negative")
        if self.tissues_with_cell_assessments > self.tissue_count:
            raise ValueError("assessed tissues cannot exceed total tissues")
        if not 0 <= self.coverage <= 1:
            raise ValueError("hand coverage must be between 0 and 1")
        for tissue in self.tissue_states:
            tissue.validate()


def build_cell_points(
    cells: Iterable[CellObject],
    assessments: Iterable[BiologicalStateAssessment] = (),
    ages: Iterable[BiologicalAgeEstimate] = (),
) -> tuple[CellLongitudinalPoint, ...]:
    cells_by_id = {cell.cell_id: cell for cell in cells}
    state_by_id: dict[str, BiologicalStateAssessment] = {}
    age_by_id: dict[str, BiologicalAgeEstimate] = {}
    for assessment in assessments:
        assessment.validate()
        if assessment.target_object_id in cells_by_id:
            state_by_id[assessment.target_object_id] = assessment
    for age in ages:
        age.validate()
        if age.target_object_id in cells_by_id:
            age_by_id[age.target_object_id] = age

    points: list[CellLongitudinalPoint] = []
    for cell in cells_by_id.values():
        state = state_by_id.get(cell.cell_id)
        age = age_by_id.get(cell.cell_id)
        if state and (state.subject_id, state.hand_id, state.timepoint_id) != (cell.subject_id, cell.hand_id, cell.timepoint_id):
            raise ValueError(f"state assessment context does not match cell {cell.cell_id}")
        if age and (age.subject_id, age.hand_id, age.timepoint_id) != (cell.subject_id, cell.hand_id, cell.timepoint_id):
            raise ValueError(f"age estimate context does not match cell {cell.cell_id}")
        points.append(CellLongitudinalPoint(
            cell_id=cell.cell_id,
            subject_id=cell.subject_id,
            hand_id=cell.hand_id,
            timepoint_id=cell.timepoint_id,
            state=state.state if state else None,
            state_confidence=state.confidence if state else None,
            biological_age_years=age.estimated_age_years if age else None,
            biological_age_interval=age.uncertainty.interval if age else None,
        ))
    return tuple(points)


def aggregate_tissue(
    tissue: TissueRegion,
    cells: Iterable[CellObject],
    assessments: Iterable[BiologicalStateAssessment] = (),
    ages: Iterable[BiologicalAgeEstimate] = (),
) -> TissueLongitudinalState:
    tissue_cells = [cell for cell in cells if cell.tissue_id == tissue.tissue_id]
    for cell in tissue_cells:
        if (cell.subject_id, cell.hand_id, cell.timepoint_id) != (tissue.subject_id, tissue.hand_id, tissue.timepoint_id):
            raise ValueError(f"cell {cell.cell_id} does not belong to tissue context")
    points = build_cell_points(tissue_cells, assessments, ages)
    assessed = [point for point in points if point.state is not None]
    state_counts: dict[str, int] = {}
    for point in assessed:
        state_counts[point.state] = state_counts.get(point.state, 0) + 1
    ages_present = [point.biological_age_years for point in points if point.biological_age_years is not None]
    intervals = [point.biological_age_interval for point in points if point.biological_age_interval is not None]
    interval = None
    if intervals:
        interval = (min(item[0] for item in intervals), max(item[1] for item in intervals))
    result = TissueLongitudinalState(
        tissue_id=tissue.tissue_id,
        subject_id=tissue.subject_id,
        hand_id=tissue.hand_id,
        timepoint_id=tissue.timepoint_id,
        cell_count=len(points),
        assessed_cell_count=len(assessed),
        state_counts=state_counts,
        state_coverage=(len(assessed) / len(points)) if points else 0.0,
        mean_biological_age_years=(sum(ages_present) / len(ages_present)) if ages_present else None,
        biological_age_interval=interval,
    )
    result.validate()
    return result


def aggregate_hand(
    subject_id: str,
    hand_id: str,
    timepoint_id: str,
    tissues: Iterable[TissueRegion],
    cells: Iterable[CellObject],
    assessments: Iterable[BiologicalStateAssessment] = (),
    ages: Iterable[BiologicalAgeEstimate] = (),
) -> HandLongitudinalState:
    tissue_list = [t for t in tissues if (t.subject_id, t.hand_id, t.timepoint_id) == (subject_id, hand_id, timepoint_id)]
    cell_list = list(cells)
    assessment_list = list(assessments)
    age_list = list(ages)
    states = tuple(aggregate_tissue(tissue, cell_list, assessment_list, age_list) for tissue in tissue_list)
    result = HandLongitudinalState(
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        tissue_count=len(tissue_list),
        tissues_with_cell_assessments=sum(1 for state in states if state.assessed_cell_count),
        tissue_states=states,
        coverage=(sum(1 for state in states if state.assessed_cell_count) / len(states)) if states else 0.0,
    )
    result.validate()
    return result
