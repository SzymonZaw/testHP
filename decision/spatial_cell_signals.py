from __future__ import annotations

"""Spatial projection of cell-level observations into a tissue coordinate frame.

This is an evidence/visualization layer. It does not diagnose disease or
recommend treatment. It answers: where are observed cell-level signals?
"""

from dataclasses import dataclass
from typing import Sequence

from backend.anatomy_foundation import CellObject, CellStateAssessment
from backend.biological_state import BiologicalAgeEstimate


@dataclass(frozen=True)
class SpatialCellSignal:
    cell_id: str
    tissue_id: str
    position: dict[str, float]
    state: str | None
    state_confidence: float | None
    biological_age_years: float | None


def project_cell_signals(
    tissue_id: str,
    cells: Sequence[CellObject],
    assessments: Sequence[CellStateAssessment] = (),
    age_estimates: Sequence[BiologicalAgeEstimate] = (),
) -> tuple[SpatialCellSignal, ...]:
    """Join cell observations with assessments while preserving cell position."""
    if not tissue_id.strip():
        raise ValueError("tissue_id is required")
    if any(cell.tissue_id != tissue_id for cell in cells):
        raise ValueError("all cells must belong to tissue_id")

    by_cell = {cell.cell_id: cell for cell in cells}
    if len(by_cell) != len(cells):
        raise ValueError("cell ids must be unique")

    state_by_cell: dict[str, CellStateAssessment] = {}
    for item in assessments:
        if item.cell_id not in by_cell:
            raise ValueError("assessment refers to a cell outside tissue_id")
        item.validate()
        if item.cell_id in state_by_cell:
            raise ValueError("multiple assessments for one cell are ambiguous")
        state_by_cell[item.cell_id] = item

    age_by_cell: dict[str, BiologicalAgeEstimate] = {}
    for item in age_estimates:
        if item.target_object_id not in by_cell:
            raise ValueError("age estimate refers to a cell outside tissue_id")
        item.validate()
        if item.target_object_id in age_by_cell:
            raise ValueError("multiple age estimates for one cell are ambiguous")
        age_by_cell[item.target_object_id] = item

    return tuple(
        SpatialCellSignal(
            cell_id=cell.cell_id,
            tissue_id=tissue_id,
            position=dict(cell.position),
            state=(state_by_cell[cell.cell_id].state if cell.cell_id in state_by_cell else None),
            state_confidence=(state_by_cell[cell.cell_id].confidence if cell.cell_id in state_by_cell else None),
            biological_age_years=(age_by_cell[cell.cell_id].estimated_age_years if cell.cell_id in age_by_cell else None),
        )
        for cell in cells
    )
