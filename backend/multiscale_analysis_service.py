from __future__ import annotations

"""Application boundary for evidence-gated cell analysis.

The service resolves the persisted hierarchy before accepting a research
assessment. It deliberately contains no clinical decision logic.
"""

from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence
from .cell_analysis import CellAnalysisInput, build_cell_age_estimate, build_cell_state_assessment
from .evidence_attachment import EvidenceAttachment, register_evidence_attachment
from .multiscale_registry import MultiscaleRegistry, register_biological_age, register_biological_state, register_cell, register_tissue


def register_cell_analysis_chain(
    registry: MultiscaleRegistry,
    *,
    cell,
    tissue,
    attachment: EvidenceAttachment,
    evidence: InterpretationEvidence,
) -> None:
    """Register a tissue/cell/evidence edge after validating the full local chain."""
    registry.add_tissue(tissue)
    registry.add_cell(cell)
    if attachment.spatial_node_id != cell.cell_id or attachment.spatial_level != "cell":
        raise ValueError("evidence attachment must target the registered cell")
    if attachment.tissue_id if hasattr(attachment, "tissue_id") else False:
        raise ValueError("unexpected tissue attachment field")
    if attachment.subject_id != cell.subject_id or attachment.hand_id != cell.hand_id or attachment.timepoint_id != cell.timepoint_id:
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
    """Create and persist state + age outputs only after hierarchy/evidence checks."""
    analysis.validate()
    if analysis.cell_id not in registry.cells:
        raise ValueError("cell analysis requires an existing registered cell")
    cell = registry.cells[analysis.cell_id]
    if (analysis.attachment.subject_id, analysis.attachment.hand_id, analysis.attachment.timepoint_id) != (cell.subject_id, cell.hand_id, cell.timepoint_id):
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
    registry.add_cell_state_assessment(
        __import__("backend.anatomy_foundation", fromlist=["CellStateAssessment"]).CellStateAssessment(
            assessment_id=state_assessment.assessment_id,
            cell_id=analysis.cell_id,
            state=state_assessment.state,
            confidence=state_assessment.confidence,
        )
    )
    register_biological_state(state_assessment)
    register_biological_age(age_estimate)
    return state_assessment, age_estimate
