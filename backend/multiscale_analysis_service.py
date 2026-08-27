from __future__ import annotations

"""Application boundary for evidence-gated cell analysis.

This layer resolves the registered hierarchy before accepting research
interpretations. It deliberately contains no clinical decision logic.
"""

from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence
from .cell_analysis import CellAnalysisInput, build_cell_age_estimate, build_cell_state_assessment
from .evidence_attachment import EvidenceAttachment, register_evidence_attachment
from .multiscale_registry import MultiscaleRegistry, register_biological_age, register_biological_state


def register_cell_analysis_chain(
    registry: MultiscaleRegistry,
    *,
    cell,
    tissue,
    attachment: EvidenceAttachment,
    evidence: InterpretationEvidence,
) -> None:
    """Validate and register one tissue -> cell -> evidence edge."""
    registry.add_tissue(tissue)
    registry.add_cell(cell)
    if attachment.spatial_node_id != cell.cell_id or attachment.spatial_level != "cell":
        raise ValueError("evidence attachment must target the registered cell")
    if (attachment.subject_id, attachment.hand_id, attachment.timepoint_id) != (
        cell.subject_id, cell.hand_id, cell.timepoint_id
    ):
        raise ValueError("evidence attachment context must match cell")
    if evidence.evidence_id != attachment.evidence_id:
        raise ValueError("evidence must match attachment")
    register_evidence_attachment(attachment)


def register_cell_research_outputs(
    registry: MultiscaleRegistry,
    analysis: CellAnalysisInput,
    *,
    state: str,
    state_assessment_id: str,
    state_confidence: float | None,
    state_assessed_at: str,
    state_provenance,
    state_uncertainty,
    age_estimate_id: str,
    estimated_age_years: float,
    age_uncertainty,
    age_assessed_at: str,
    age_provenance,
    model_id: str | None = None,
    model_version: str | None = None,
) -> tuple[BiologicalStateAssessment, BiologicalAgeEstimate]:
    """Build and persist state + age only after all evidence gates pass."""
    analysis.validate()
    cell = registry.cells.get(analysis.cell_id)
    if cell is None:
        raise ValueError("cell analysis requires an existing registered cell")
    if (analysis.attachment.subject_id, analysis.attachment.hand_id, analysis.attachment.timepoint_id) != (
        cell.subject_id, cell.hand_id, cell.timepoint_id
    ):
        raise ValueError("analysis context must match the registered cell")

    state_assessment = build_cell_state_assessment(
        analysis,
        assessment_id=state_assessment_id,
        state=state,
        confidence=state_confidence,
        assessed_at=state_assessed_at,
        provenance=state_provenance,
        uncertainty=state_uncertainty,
        model_id=model_id,
        model_version=model_version,
    )
    age_estimate = build_cell_age_estimate(
        analysis,
        estimate_id=age_estimate_id,
        estimated_age_years=estimated_age_years,
        uncertainty=age_uncertainty,
        assessed_at=age_assessed_at,
        provenance=age_provenance,
        model_id=model_id,
        model_version=model_version,
    )

    # Persist only after both derived objects validate. Each registry function
    # is idempotent on its own; callers needing cross-row atomicity should use
    # the database transaction boundary before promoting this to production.
    register_biological_state(state_assessment)
    register_biological_age(age_estimate)
    return state_assessment, age_estimate
