"""
Tissue state representation for the digital twin.

This module stores tissue-level biological measurements obtained from
image analysis, WSI analysis, morphology analysis, pathology models, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class TissueState:
    """
    Represents the current tissue-level state of a subject.
    """

    tissue_type: str = "skin"

    thickness: Optional[float] = None
    density: Optional[float] = None

    collagen_disorganization: Optional[float] = None
    vascular_abnormality: Optional[float] = None
    inflammation_score: Optional[float] = None
    fibrosis_score: Optional[float] = None
    pigmentation_score: Optional[float] = None

    lesion_burden: Optional[float] = None
    tissue_abnormality_score: Optional[float] = None

    morphology_score: Optional[float] = None
    pathology_score: Optional[float] = None

    confidence: float = 0.0

    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    metadata: Dict[str, Any] = field(default_factory=dict)

    def update(
        self,
        values: Dict[str, Any],
        confidence: Optional[float] = None,
    ) -> None:
        """
        Update tissue state from a dictionary of measurements.
        """

        for key, value in values.items():

            if key == "metadata":
                if isinstance(value, dict):
                    self.metadata.update(value)
                continue

            if hasattr(self, key):
                setattr(self, key, value)

        if confidence is not None:
            self.confidence = float(confidence)

        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tissue state to a serializable dictionary.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TissueState":
        """
        Create TissueState from dictionary.
        """
        return cls(**data)

    def summary(self) -> Dict[str, Any]:
        """
        Return a compact tissue summary.
        """

        return {
            "tissue_type": self.tissue_type,
            "thickness": self.thickness,
            "inflammation_score": self.inflammation_score,
            "fibrosis_score": self.fibrosis_score,
            "collagen_disorganization": self.collagen_disorganization,
            "vascular_abnormality": self.vascular_abnormality,
            "tissue_abnormality_score": self.tissue_abnormality_score,
            "pathology_score": self.pathology_score,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }