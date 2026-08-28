"""
Cellular state representation for the digital twin.

Stores measurements derived from Cellpose, microscopy, single-cell RNA
analysis, cell morphology analysis, and other cellular assays.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class CellState:
    """Represents the observed state of an individual or aggregated cell."""

    cell_id: Optional[str] = None
    cell_type: Optional[str] = None
    health_state: Optional[str] = None
    biological_age: Optional[float] = None
    biological_age_range: Optional[Dict[str, float]] = None

    total_cell_count: Optional[int] = None
    cell_density: Optional[float] = None
    mean_cell_area: Optional[float] = None
    mean_nuclear_area: Optional[float] = None

    abnormal_cell_fraction: Optional[float] = None
    senescent_cell_fraction: Optional[float] = None
    immune_cell_fraction: Optional[float] = None
    proliferating_cell_fraction: Optional[float] = None
    apoptotic_cell_fraction: Optional[float] = None

    cell_diversity: Optional[float] = None
    cellular_abnormality_score: Optional[float] = None
    function_score: Optional[float] = None

    biomarkers: Dict[str, Any] = field(default_factory=dict)
    abnormalities: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update(self, values: Dict[str, Any], confidence: Optional[float] = None) -> None:
        """Update observed cellular state without inventing missing values."""
        for key, value in values.items():
            if key in {"metadata", "biomarkers"} and isinstance(value, dict):
                getattr(self, key).update(value)
            elif key in {"abnormalities", "evidence"} and isinstance(value, list):
                setattr(self, key, value)
            elif hasattr(self, key):
                setattr(self, key, value)

        if confidence is not None:
            self.confidence = float(confidence)
        self.timestamp = datetime.utcnow().isoformat()

    def add_evidence(
        self,
        source: str,
        observation: str,
        value: Any = None,
        confidence: Optional[float] = None,
    ) -> None:
        """Attach an auditable observation supporting the current state."""
        item: Dict[str, Any] = {"source": source, "observation": observation}
        if value is not None:
            item["value"] = value
        if confidence is not None:
            item["confidence"] = float(confidence)
        self.evidence.append(item)

    def add_abnormality(
        self,
        kind: str,
        severity: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an observed cellular abnormality without assigning a diagnosis."""
        item: Dict[str, Any] = {"kind": kind}
        if severity is not None:
            item["severity"] = severity
        if details:
            item["details"] = dict(details)
        self.abnormalities.append(item)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CellState":
        return cls(**data)

    def summary(self) -> Dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "cell_type": self.cell_type,
            "health_state": self.health_state,
            "biological_age": self.biological_age,
            "biological_age_range": self.biological_age_range,
            "total_cell_count": self.total_cell_count,
            "cell_density": self.cell_density,
            "abnormal_cell_fraction": self.abnormal_cell_fraction,
            "senescent_cell_fraction": self.senescent_cell_fraction,
            "immune_cell_fraction": self.immune_cell_fraction,
            "proliferating_cell_fraction": self.proliferating_cell_fraction,
            "apoptotic_cell_fraction": self.apoptotic_cell_fraction,
            "cellular_abnormality_score": self.cellular_abnormality_score,
            "function_score": self.function_score,
            "confidence": self.confidence,
            "evidence_count": len(self.evidence),
            "abnormality_count": len(self.abnormalities),
            "timestamp": self.timestamp,
        }
