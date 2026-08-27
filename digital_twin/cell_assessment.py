"""Structured, evidence-aware assessment of an individual cell.

This layer stores observations and model outputs; it does not make clinical
diagnoses or treatment recommendations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Evidence:
    """One measurable/model-derived reason supporting an assessment."""

    source: str
    feature: str
    value: Any
    interpretation: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CellAssessment:
    """Current assessment of one cell, separated from raw cell state."""

    cell_id: str
    observed_at: datetime
    health_state: str = "unknown"
    health_score: Optional[float] = None
    biological_age: Optional[float] = None
    age_confidence: Optional[float] = None
    abnormality_score: Optional[float] = None
    uncertainty: Optional[float] = None
    evidence: List[Evidence] = field(default_factory=list)
    model_metadata: Dict[str, Any] = field(default_factory=dict)

    def add_evidence(self, evidence: Evidence) -> None:
        self.evidence.append(evidence)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["observed_at"] = self.observed_at.isoformat()
        data["evidence"] = [item.to_dict() for item in self.evidence]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CellAssessment":
        raw = dict(data)
        raw["observed_at"] = datetime.fromisoformat(raw["observed_at"])
        raw["evidence"] = [Evidence(**item) for item in raw.get("evidence", [])]
        return cls(**raw)
