"""
Cellular state representation for the digital twin.

Stores measurements derived from Cellpose, microscopy,
single-cell RNA analysis, cell morphology analysis, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class CellState:
    """
    Represents the current cellular state of a subject.
    """

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
        Update cellular state.
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
        Convert to dictionary.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CellState":
        """
        Create CellState from dictionary.
        """
        return cls(**data)

    def summary(self) -> Dict[str, Any]:
        """
        Return compact cellular summary.
        """

        return {
            "total_cell_count": self.total_cell_count,
            "cell_density": self.cell_density,
            "abnormal_cell_fraction": self.abnormal_cell_fraction,
            "senescent_cell_fraction": self.senescent_cell_fraction,
            "immune_cell_fraction": self.immune_cell_fraction,
            "proliferating_cell_fraction": self.proliferating_cell_fraction,
            "cellular_abnormality_score": self.cellular_abnormality_score,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }