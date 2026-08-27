from __future__ import annotations

"""Application boundary for evidence-gated cell analysis.

All PostgreSQL writes belonging to one cell-analysis result are committed as
one unit. This layer contains no clinical decision logic.
"""

from .anatomy_foundation import CellStateAssessment
from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence
from .cell_analysis import CellAnalysisInput, build_cell_age_estimate, build_cell_state_assessment
from .database import connect, ensure_schema
from .evidence_attachment import EvidenceAttachment, _register_evidence_attachment_conn, ensure_evidence_attachment_schema, register_evidence_attachment
from .multiscale_registry import (
    MultiscaleRegistry,
    _register_biological_age_conn,
    _register_biological_state_conn,
    _register_cell_conn,
    _register_tissue_conn,
    register_biological_age,
    register_biological_state,
)


def register_cell_analysis_chain(registry: MultiscaleRegistry, *, cell, tissue, attachment: EvidenceAttachment, evidence: InterpretationEvidence) -> None:
    """Validate and register one tissue -> cell -> evidence edge."""
    registry.add_tissue(tissue)
    registry.add_cell(cell)
    if attachment.spatial_node_id != cell.cell_id or attachment.spatial_level != "cell":
        raise ValueError("evidence attachment must target the registered cell")
    if (attachment.subject_id, attachment.hand_id, attachment.timepoint_id) != (cell.subject_id, cell.hand_id, cell.timepoint_id):
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
    """Atomically persist the tissue -> cell -> evidence -> state -> age chain."""
    analysis.validate()
    cell = registry.cells.get(analysis.cell_id)
    if cell is None:
        raise ValueError("cell analysis requires an existing registered cell")
    if (analysis.attachment.subject_id, analysis.attachment.hand_id, analysis.attachment.timepoint_id) != (cell.subject_id, cell.hand_id, cell.timepoint_id):
        raise ValueError("analysis context must match the registered cell")

    state_assessment = build_cell_state_assessment(
        analysis, assessment_id=state_assessment_id, state=state, confidence=state_confidence,
        assessed_at=state_assessed_at, provenance=state_provenance, uncertainty=state_uncertainty,
        model_id=model_id, model_version=model_version,
    )
    age_estimate = build_cell_age_estimate(
        analysis, estimate_id=age_estimate_id, estimated_age_years=estimated_age_years,
        uncertainty=age_uncertainty, assessed_at=age_assessed_at, provenance=age_provenance,
        model_id=model_id, model_version=model_version,
    )

    # Schema creation is deliberately outside the data transaction because
    # ensure_schema() and ensure_evidence_attachment_schema() commit their DDL.
    ensure_schema()
    ensure_evidence_attachment_schema()

    tissue = registry.tissues.get(cell.tissue_id)
    if tissue is None:
        raise ValueError("cell analysis requires an existing registered tissue")
    registry.add_cell_state_assessment(CellStateAssessment(
        assessment_id=state_assessment.assessment_id,
        cell_id=cell.cell_id,
        state=state_assessment.state,
        confidence=state_assessment.confidence,
    ))
    analysis.attachment.validate()
    if analysis.attachment.spatial_node_id != cell.cell_id or analysis.attachment.spatial_level != "cell":
        raise ValueError("evidence attachment must target the registered cell")
    if analysis.evidence.evidence_id != analysis.attachment.evidence_id:
        raise ValueError("evidence must match attachment")

    with connect() as conn:
        _register_tissue_conn(conn, tissue)
        _register_cell_conn(conn, cell)
        _register_evidence_attachment_conn(conn, analysis.attachment)
        _register_biological_state_conn(conn, state_assessment)
        _register_biological_age_conn(conn, age_estimate)

    return state_assessment, age_estimate
