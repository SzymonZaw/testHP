from __future__ import annotations

"""Evidence-first summaries across the hand -> tissue -> cell hierarchy.

The summary is a decision-support contract, not a diagnosis or treatment
recommendation. It keeps raw cell assessments intact and reports only
transparent aggregates plus an explicit attention band.
"""

from dataclasses import dataclass
from typing import Literal, Sequence

from .anatomy_foundation import CellObject, TissueRegion
from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment

AttentionBand = Literal["no_signal", "monitor", "review"]


@dataclass(frozen=True)
class TissueBiologicalSummary:
    tissue_id: str
    cell_count: int
    assessed_cell_count: int
    state_counts: dict[str, int]
    mean_confidence: float | None
    estimated_age_years: float | None
    age_interval: tuple[float, float] | None
    attention_band: AttentionBand

    def to_dict(self) -> dict[str, object]:
        return {
            "tissue_id": self.tissue_id,
            "cell_count": self.cell_count,
            "assessed_cell_count": self.assessed_cell_count,
            "state_counts": dict(self.state_counts),
            "mean_confidence": self.mean_confidence,
            "estimated_age_years": self.estimated_age_years,
            "age_interval": self.age_interval,
            "attention_band": self.attention_band,
        }


def summarize_tissue(
    tissue: TissueRegion,
    cells: Sequence[CellObject],
    assessments: Sequence[BiologicalStateAssessment] = (),
    age_estimates: Sequence[BiologicalAgeEstimate] = (),
) -> TissueBiologicalSummary:
    """Build a transparent tissue-level summary from registered cell data.

    Only assessments explicitly attached to cells in ``tissue`` contribute.
    ``review`` means that the observed pattern deserves expert review; it is
    intentionally not a diagnosis or a treatment recommendation.
    """
    tissue.validate()
    tissue_cells = [cell for cell in cells if cell.tissue_id == tissue.tissue_id]
    cell_ids = {cell.cell_id for cell in tissue_cells}

    selected = [item for item in assessments if item.target_object_id in cell_ids]
    for item in selected:
        item.validate()

    state_counts: dict[str, int] = {}
    confidences: list[float] = []
    for item in selected:
        state_counts[item.state] = state_counts.get(item.state, 0) + 1
        if item.confidence is not None:
            confidences.append(item.confidence)

    mean_confidence = sum(confidences) / len(confidences) if confidences else None

    selected_ages = [item for item in age_estimates if item.target_object_id in cell_ids]
    for item in selected_ages:
        item.validate()
    if selected_ages:
        ages = [item.estimated_age_years for item in selected_ages]
        estimated_age = sum(ages) / len(ages)
        lows: list[float] = []
        highs: list[float] = []
        for item in selected_ages:
            interval = item.uncertainty.interval
            if interval is not None:
                lows.append(float(interval[0]))
                highs.append(float(interval[1]))
        age_interval = (min(lows), max(highs)) if lows and highs else None
    else:
        estimated_age = None
        age_interval = None

    pathological = state_counts.get("pathological", 0)
    suspicious = state_counts.get("suspicious", 0)
    atypical = state_counts.get("atypical", 0)
    assessed = len(selected)
    if pathological or suspicious:
        attention_band: AttentionBand = "review"
    elif atypical:
        attention_band = "monitor"
    else:
        attention_band = "no_signal"

    return TissueBiologicalSummary(
        tissue_id=tissue.tissue_id,
        cell_count=len(tissue_cells),
        assessed_cell_count=assessed,
        state_counts=state_counts,
        mean_confidence=mean_confidence,
        estimated_age_years=estimated_age,
        age_interval=age_interval,
        attention_band=attention_band,
    )
