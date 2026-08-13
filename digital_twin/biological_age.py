"""
Biological age representation.

This module stores biological-age estimates and their contributing
modalities.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class BiologicalAge:
    """
    Represents the estimated biological age of a subject.
    """

    chronological_age: Optional[float] = None

    biological_age: Optional[float] = None

    age_acceleration: Optional[float] = None

    confidence: float = 0.0

    tissue_contribution: Optional[float] = None
    cellular_contribution: Optional[float] = None
    rna_contribution: Optional[float] = None
    morphology_contribution: Optional[float] = None
    hand_contribution: Optional[float] = None

    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_age_acceleration(self) -> Optional[float]:
        """
        Calculate biological-age acceleration.

        Positive value:
            biological age > chronological age

        Negative value:
            biological age < chronological age
        """

        if (
            self.biological_age is None
            or self.chronological_age is None
        ):
            return None

        self.age_acceleration = (
            self.biological_age - self.chronological_age
        )

        return self.age_acceleration

    def update(
        self,
        biological_age: Optional[float] = None,
        chronological_age: Optional[float] = None,
        confidence: Optional[float] = None,
        contributions: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Update biological-age information.
        """

        if biological_age is not None:
            self.biological_age = float(biological_age)

        if chronological_age is not None:
            self.chronological_age = float(chronological_age)

        if confidence is not None:
            self.confidence = float(confidence)

        if contributions:

            for key, value in contributions.items():

                attribute = f"{key}_contribution"

                if hasattr(self, attribute):
                    setattr(self, attribute, float(value))

        self.calculate_age_acceleration()

        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BiologicalAge":
        """
        Create BiologicalAge from dictionary.
        """
        return cls(**data)

    def summary(self) -> Dict[str, Any]:
        """
        Return compact biological-age summary.
        """

        return {
            "chronological_age": self.chronological_age,
            "biological_age": self.biological_age,
            "age_acceleration": self.age_acceleration,
            "confidence": self.confidence,
            "tissue_contribution": self.tissue_contribution,
            "cellular_contribution": self.cellular_contribution,
            "rna_contribution": self.rna_contribution,
            "morphology_contribution": self.morphology_contribution,
            "hand_contribution": self.hand_contribution,
            "timestamp": self.timestamp,
        }