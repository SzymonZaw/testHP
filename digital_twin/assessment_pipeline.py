"""Compose evidence, assessment, trend, hierarchy and observation priority."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .assessment_trends import compare_cell_assessments
from .data_quality import Uncertainty
from .observation_priority import prioritize_observation


def build_assessment_view(twin: Any, cell_id: str, previous_assessment: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    assessment = twin.get_cell_assessment(cell_id)
    if assessment is None:
        return None

    evidence = []
    evidence_by_cell = twin.metadata.get("evidence", {})
    if isinstance(evidence_by_cell, dict):
        evidence = evidence_by_cell.get(cell_id, []) or []
    evidence_summary = {"count": len(evidence)}
    if evidence:
        from .evidence import evidence_summary as summarize
        evidence_summary = summarize(evidence)

    confidence = float(getattr(assessment, "confidence", 0.0))
    uncertainty = Uncertainty(confidence=confidence, reason="cell_assessment").to_dict()
    trend = compare_cell_assessments(previous_assessment, assessment).to_dict() if previous_assessment else None
    abnormality = getattr(assessment, "abnormality", None)
    trend_delta = getattr(trend, "abnormality_delta", None) if trend else None
    priority = prioritize_observation(cell_id, confidence, 1.0, abnormality, trend_delta).to_dict()

    return {
        "target": twin.cell_spatial_context(cell_id),
        "assessment": assessment.to_dict(),
        "evidence": evidence_summary,
        "quality": evidence_summary,
        "uncertainty": uncertainty,
        "trend": trend,
        "hierarchy": twin.hierarchical_assessment(),
        "observation_priority": priority,
    }
