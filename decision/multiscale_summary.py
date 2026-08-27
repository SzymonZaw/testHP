from __future__ import annotations

"""Deterministic aggregation from cell assessments to tissue-level signals.

This module is deliberately a decision-support boundary: it summarizes model
outputs and uncertainty, but does not diagnose disease or prescribe treatment.
"""

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Sequence

from backend.anatomy_foundation import CellObject, CellStateAssessment
from backend.biological_state import BiologicalAgeEstimate


@dataclass(frozen=True)
class TissueMultiscaleSummary:
    tissue_id: str
    cell_count: int
    state_counts: dict[str, int]
    assessed_fraction: float
    mean_cell_confidence: float | None
    mean_biological_age_years: float | None
    biological_age_min_years: float | None
    biological_age_max_years: float | None
    signal: str


def summarize_tissue(
    tissue_id: str,
    cells: Sequence[CellObject],
    assessments: Sequence[CellStateAssessment],
    age_estimates: Sequence[BiologicalAgeEstimate] = (),
) -> TissueMultiscaleSummary:
    """Aggregate cell-level outputs for one tissue without inventing labels.

    ``signal`` is only a coarse data-quality/observation signal. It is not a
    clinical recommendation. A pathological observation becomes
    ``pathology_observed``; missing or contradictory coverage becomes
    ``insufficient_evidence``; otherwise the result is ``observed``.
    """
    if not tissue_id.strip():
        raise ValueError("tissue_id is required")
    if any(cell.tissue_id != tissue_id for cell in cells):
        raise ValueError("all cells must belong to tissue_id")

    cell_ids = {cell.cell_id for cell in cells}
    relevant = [item for item in assessments if item.cell_id in cell_ids]
    if any(item.cell_id not in cell_ids for item in assessments):
        raise ValueError("assessment refers to a cell outside tissue_id")

    for item in relevant:
        item.validate()
    for item in age_estimates:
        item.validate()
        if item.target_object_id not in cell_ids:
            raise ValueError("age estimate refers to a cell outside tissue_id")

    counts = Counter(item.state for item in relevant)
    confidences = [item.confidence for item in relevant if item.confidence is not None]
    ages = [item.estimated_age_years for item in age_estimates]

    assessed_fraction = len(relevant) / len(cells) if cells else 0.0
    if not cells or assessed_fraction == 0.0:
        signal = "insufficient_evidence"
    elif counts.get("pathological", 0) > 0:
        signal = "pathology_observed"
    elif assessed_fraction < 1.0:
        signal = "insufficient_evidence"
    else:
        signal = "observed"

    return TissueMultiscaleSummary(
        tissue_id=tissue_id,
        cell_count=len(cells),
        state_counts=dict(counts),
        assessed_fraction=assessed_fraction,
        mean_cell_confidence=mean(confidences) if confidences else None,
        mean_biological_age_years=mean(ages) if ages else None,
        biological_age_min_years=min(ages) if ages else None,
        biological_age_max_years=max(ages) if ages else None,
        signal=signal,
    )
