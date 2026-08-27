"""Anatomical and spatial location for hand digital-twin observations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class AnatomicalLocation:
    """Hierarchical and optional spatial location of an observed structure."""

    hand_side: Optional[str] = None
    region_id: Optional[str] = None
    tissue_id: Optional[str] = None
    coordinates: Optional[Tuple[float, float, float]] = None
    coordinate_system: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.hand_side is not None and self.hand_side not in {"left", "right"}:
            raise ValueError("hand_side must be 'left', 'right', or None")
        if self.coordinates is not None:
            if len(self.coordinates) != 3:
                raise ValueError("coordinates must contain exactly three values")
            object.__setattr__(
                self,
                "coordinates",
                tuple(float(value) for value in self.coordinates),
            )
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hand_side": self.hand_side,
            "region_id": self.region_id,
            "tissue_id": self.tissue_id,
            "coordinates": list(self.coordinates) if self.coordinates is not None else None,
            "coordinate_system": self.coordinate_system,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }
