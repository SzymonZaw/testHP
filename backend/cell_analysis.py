from __future__ import annotations

"""Evidence-gated research analysis for an individual cell.

This layer turns already attached observations into explicit research claims.
It does not diagnose disease, prescribe treatment, or infer an intervention.
"""

from dataclasses import dataclass
from typing import Any

from .biological_state import BiologicalAgeEstimate, BiologicalStateAssessment, InterpretationEvidence
from .data_foundation import Provenance, Uncertainty
from .evidence_attachment import EvidenceAttachment


@dataclass(frozen=True)
class CellAnalysisInput:
    cell_id: str
    attachment: EvidenceAttachment
    evidence: InterpretationEvidence

    def validate(self) -> None:
        self.attachment.validate()
        self.evidence.validate()
        if self.attachment.spatial_level != "cell":
            raise ValueError("cell analysis requires evidence attached at cell level")
        if self.attachment.spatial_node_id != self.cell_id:
            raise ValueError("cell analysis evidence must target the supplied cell")
        if self.evidence.evidence_id != self.attachment.evidence_id:
            raise ValueError("analysis evidence must match the attached evidence")


def build_cell_state_assessment(
    analysis: CellAnalysisInput,
    *,
    assessment_id: str,
    state: str,
    confidence: float | None,
    assessed_at: str,
    provenance: Provenance,
    uncertainty: Uncertainty,
    model_id: str | None = None,
    model_version: str | None = None,
) -> BiologicalStateAssessment:
    """Build a research state assessment only from explicitly attached evidence."""
    analysis.validate()
    assessment = BiologicalStateAssessment(
        assessment_id=assessment_id,
        subject_id=analysis.attachment.subject_id,
        hand_id=analysis.attachment.hand_id,
        timepoint_id=analysis.attachment.timepoint_id,
        target_object_id=analysis.cell_id,
        state=state,
        confidence=confidence,
        evidence=(analysis.evidence,),
        uncertainty=uncertainty,
        provenance=provenance,
        assessed_at=assessed_at,
        model_id=model_id,
        model_version=model_version,
    )
    assessment.validate()
    return assessment


def build_cell_age_estimate(
    analysis: CellAnalysisInput,
    *,
    estimate_id: str,
    estimated_age_years: float,
    uncertainty: Uncertainty,
    assessed_at: str,
    provenance: Provenance,
    model_id: str | None = None,
    model_version: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> BiologicalAgeEstimate:
    """Build a biological-age research estimate from the same explicit evidence."""
    analysis.validate()
    estimate = BiologicalAgeEstimate(
        estimate_id=estimate_id,
        subject_id=analysis.attachment.subject_id,
        hand_id=analysis.attachment.hand_id,
        timepoint_id=analysis.attachment.timepoint_id,
        target_object_id=analysis.cell_id,
        estimated_age_years=estimated_age_years,
        uncertainty=uncertainty,
        evidence=(analysis.evidence,),
        provenance=provenance,
        assessed_at=assessed_at,
        model_id=model_id,
        model_version=model_version,
        metadata=metadata or {},
    )
    estimate.validate()
    return estimate
