from __future__ import annotations

from typing import Any

from .decision_engine import DecisionEngine


def make_pipeline_decision(*, evaluation: dict[str, Any], quality: float, risk: float = 0.0, abnormality: float = 0.0, pathology: float = 0.0, temporal_values: list[float] | None = None) -> dict[str, Any]:
    """Stage 9 adapter: turns pipeline evidence into a conservative decision.

    This is decision support only; it does not diagnose disease.
    """
    if evaluation.get("status") != "ready":
        return {"decision": "insufficient_evidence", "confidence": 0.0, "safety_allowed": False, "reasons": evaluation.get("limitations", [])}
    result = DecisionEngine().evaluate_dict(
        model_confidence=min(1.0, float(evaluation.get("readiness", 0.0))),
        data_quality=quality,
        temporal_consistency=1.0 if temporal_values and len(temporal_values) >= 2 else 0.5,
        multimodal_consistency=1.0,
        data_completeness=min(1.0, float(evaluation.get("readiness", 0.0))),
        risk_score=risk,
        abnormality_score=abnormality,
        pathology_score=pathology,
        temporal_values=temporal_values,
        data_complete=True,
        multimodal_consistent=True,
        temporal_data_available=bool(temporal_values and len(temporal_values) >= 2),
    )
    return result
