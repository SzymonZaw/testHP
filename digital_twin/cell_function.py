"""Functional-state representation for individual cells."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CellFunctionState:
    """Coarse functional state derived from measurable cellular signals."""

    status: str
    score: Optional[float]
    confidence: float
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "score": self.score,
            "confidence": self.confidence,
            "evidence": dict(self.evidence),
        }


def classify_cell_function(
    function_score: Optional[float],
    confidence: float = 0.0,
    evidence: Optional[Dict[str, Any]] = None,
) -> CellFunctionState:
    """Classify cellular function without inferring a disease or treatment."""
    bounded_confidence = max(0.0, min(1.0, float(confidence)))
    if function_score is None or bounded_confidence < 0.5:
        return CellFunctionState("unknown", None, bounded_confidence, evidence or {})

    score = max(0.0, min(1.0, float(function_score)))
    if score >= 0.75:
        status = "preserved"
    elif score >= 0.4:
        status = "reduced"
    else:
        status = "impaired"
    return CellFunctionState(status, score, bounded_confidence, evidence or {})
