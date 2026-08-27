"""Structured evidence records for research-only biological assessments."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from .data_quality import DataQuality, combine_confidence


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
    data_quality: Optional[DataQuality] = None

    def effective_confidence(self) -> float:
        return combine_confidence(self.confidence, self.data_quality)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["observed_at"] = self.observed_at.isoformat()
        data["effective_confidence"] = self.effective_confidence()
        if self.data_quality:
            data["data_quality"] = self.data_quality.to_dict()
        return data


def aggregate_evidence_confidence(evidence: list[Evidence]) -> float:
    if not evidence:
        return 0.0
    return sum(item.effective_confidence() for item in evidence) / len(evidence)


def evidence_summary(evidence: list[Evidence]) -> Dict[str, Any]:
    confidence = aggregate_evidence_confidence(evidence)
    return {
        "count": len(evidence),
        "confidence": confidence,
        "uncertainty": 1.0 - confidence,
        "source_types": sorted({item.source_type for item in evidence}),
        "features": sorted({item.feature for item in evidence}),
    }
