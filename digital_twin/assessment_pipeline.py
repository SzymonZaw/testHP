"""Compose evidence, assessment, trend, hierarchy and observation priority."""
from __future__ import annotations

from typing import Any, Dict, Optional

from .assessment_trends import compare_cell_assessments
from .data_quality import Uncertainty
from .observation_priority import prioritize_observation
from .evidence_assessment import assessment_inputs


def build_assessment_view(twin: Any, cell_id: str, previous_assessment: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    assessment = twin.get_cell_assessment(cell_id)
    if assessment is None:
        return None

    evidence = twin.get_cell_evidence(cell_id) if hasattr(twin, "get_cell_evidence") else []
    evidence_inputs = assessment_inputs(evidence)

    confidence = float(getattr(assessment, "confidence", 0.0))
    uncertainty = Uncertainty(confidence=confidence, reason="cell_assessment").to_dict()
    trend = compare_cell_assessments(previous_assessment, assessment).to_dict() if previous_assessment else None
    abnormality = getattr(assessment, "abnormality", None)
    trend_delta = trend.get("abnormality_delta") if isinstance(trend, dict) else None
    priority = prioritize_observation(cell_id, confidence, 1.0, abnormality, trend_delta).to_dict()

    return {
        "target": twin.cell_spatial_context(cell_id),
        "assessment": assessment.to_dict(),
        "evidence": {
            **evidence_inputs,
            "items": [item.to_dict() for item in evidence],
        },
        "quality": {
            "mean": evidence_inputs["quality"],
            "confidence": evidence_inputs["confidence"],
            "uncertainty": evidence_inputs["uncertainty"],
        },
        "uncertainty": uncertainty,
        "trend": trend,
        "hierarchy": twin.hierarchical_assessment(),
        "observation_priority": priority,
    }
