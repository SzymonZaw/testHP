"""Structured evidence records for research-only biological assessments."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Evidence:
    """A traceable input supporting an assessment; not a diagnosis."""

    evidence_id: str
    source_type: str
    source_id: str
    observed_at: datetime
    feature: str
    value: Any
    unit: Optional[str] = None
    quality: Optional[float] = None
    confidence: float = 0.0
    provenance: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["observed_at"] = self.observed_at.isoformat()
        return data


def aggregate_evidence_confidence(evidence: list[Evidence]) -> float:
    if not evidence:
        return 0.0
    weights = [max(0.0, min(1.0, item.confidence)) for item in evidence]
    return sum(weights) / len(weights)


def evidence_summary(evidence: list[Evidence]) -> Dict[str, Any]:
    return {
        "count": len(evidence),
        "confidence": aggregate_evidence_confidence(evidence),
        "source_types": sorted({item.source_type for item in evidence}),
        "features": sorted({item.feature for item in evidence}),
    }
