from __future__ import annotations

"""Evidence-first cell-state assessment contracts.

This module does not classify cells by itself. It validates the relationship
between a cell object and a model-produced state assessment so that a future
cell-analysis model can plug into the digital-twin chain without losing
identity, provenance or uncertainty.
"""

from .anatomy_foundation import CellObject, CellState
from .data_foundation import Provenance
from .anatomy_foundation import Evidence


def build_cell_state_assessment(
    cell: CellObject,
    *,
    assessment_id: str,
    state: CellState,
    confidence: float | None,
    evidence: tuple[Evidence, ...],
    provenance: Provenance,
    assessed_at: str,
):
    """Build a validated cell-level state assessment.

    The caller supplies the model output. This function only enforces that the
    assessment belongs to the supplied cell and that every evidence item is
    traceable to source data. No clinical diagnosis is inferred here.
    """
    cell.validate()
    if not assessment_id.strip():
        raise ValueError("assessment_id is required")
    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if not evidence:
        raise ValueError("cell state assessment requires evidence")
    if not assessed_at.strip():
        raise ValueError("assessed_at is required")

    for item in evidence:
        if not item.evidence_id.strip():
            raise ValueError("evidence_id is required")
        if not item.source_data_ids:
            raise ValueError("cell evidence requires source_data_ids")
        if item.confidence is not None and not 0 <= item.confidence <= 1:
            raise ValueError("evidence confidence must be between 0 and 1")

    # Keep the assessment tied to the exact cell identity and source context.
    from .anatomy_foundation import CellStateAssessment

    assessment = CellStateAssessment(
        assessment_id=assessment_id,
        cell_id=cell.cell_id,
        state=state,
        confidence=confidence,
        evidence=evidence,
        provenance=provenance,
        assessed_at=assessed_at,
    )
    assessment.validate()
    return assessment
