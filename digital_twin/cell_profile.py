"""Unified per-cell profile for the hand digital twin."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from .anatomical_location import AnatomicalLocation
from .cell_function import CellFunctionState, classify_cell_function
from .cell_health import CellHealthState, classify_cell_health
from .cell_state import CellState


@dataclass(frozen=True)
class CellProfile:
    """Single-cell state combining health, age, function, and location."""

    cell_id: str
    tissue_id: Optional[str] = None
    cell_type: Optional[str] = None
    biological_age: Optional[float] = None
    health: CellHealthState = field(default_factory=lambda: CellHealthState("unknown", None, 0.0, {}))
    function: CellFunctionState = field(default_factory=lambda: CellFunctionState("unknown", None, 0.0, {}))
    confidence: float = 0.0
    observed_at: Optional[str] = None
    location: Optional[AnatomicalLocation] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "tissue_id": self.tissue_id,
            "cell_type": self.cell_type,
            "biological_age": self.biological_age,
            "health": self.health.to_dict(),
            "function": self.function.to_dict(),
            "confidence": self.confidence,
            "observed_at": self.observed_at,
            "location": self.location.to_dict() if self.location else None,
            "metadata": dict(self.metadata),
        }

    def to_cell_state(self) -> CellState:
        """Project the profile into the canonical cellular-state representation."""
        health_state = self.health.state if self.health else "unknown"
        functional_state = self.function.state if self.function else "unknown"
        return CellState(
            cell_id=self.cell_id,
            cell_type=self.cell_type,
            biological_age=self.biological_age,
            health_state=health_state,
            functional_state=functional_state,
            confidence=self.confidence,
            timestamp=self.observed_at or "",
            metadata={"tissue_id": self.tissue_id, **self.metadata},
        )


def build_cell_profile(
    cell_id: str,
    *,
    biological_age: Optional[float] = None,
    health_markers: Optional[Mapping[str, float]] = None,
    function_score: Optional[float] = None,
    confidence: float = 0.0,
    tissue_id: Optional[str] = None,
    cell_type: Optional[str] = None,
    observed_at: Optional[str] = None,
    location: Optional[AnatomicalLocation] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> CellProfile:
    """Construct a cell profile while keeping uncertainty explicit."""
    bounded_confidence = max(0.0, min(1.0, float(confidence)))
    health = classify_cell_health(health_markers or {}, bounded_confidence)
    function = classify_cell_function(function_score, bounded_confidence)
    return CellProfile(
        cell_id=cell_id,
        tissue_id=tissue_id,
        cell_type=cell_type,
        biological_age=biological_age,
        health=health,
        function=function,
        confidence=bounded_confidence,
        observed_at=observed_at,
        location=location,
        metadata=metadata or {},
    )
