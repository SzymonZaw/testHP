"""Individual-cell state and longitudinal history."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class IndividualCellState:
    """Observed state of one cell at one point in time."""

    cell_id: str
    observed_at: datetime
    morphology: Dict[str, Any] = field(default_factory=dict)
    biomarkers: Dict[str, Any] = field(default_factory=dict)
    proliferation: Optional[float] = None
    senescence: Optional[float] = None
    apoptosis: Optional[float] = None
    abnormality: Optional[float] = None
    biological_age: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["observed_at"] = self.observed_at.isoformat()
        return data


@dataclass(frozen=True)
class CellTrend:
    """Observed longitudinal direction; not a clinical diagnosis."""

    cell_id: str
    direction: str
    age_delta: Optional[float]
    abnormality_delta: Optional[float]
    senescence_delta: Optional[float]
    confidence: float
    observations: int
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CellTimeline:
    """Chronological state history for individual cells."""

    states: Dict[str, List[IndividualCellState]] = field(default_factory=dict)

    def add(self, state: IndividualCellState) -> None:
        history = self.states.setdefault(state.cell_id, [])
        history.append(state)
        history.sort(key=lambda item: item.observed_at)

    def get(self, cell_id: str) -> List[IndividualCellState]:
        return list(self.states.get(cell_id, []))

    def latest(self, cell_id: str) -> Optional[IndividualCellState]:
        history = self.states.get(cell_id, [])
        return history[-1] if history else None

    def change(self, cell_id: str, field_name: str) -> Optional[float]:
        """Return latest minus earliest numeric value for a tracked field."""
        history = self.states.get(cell_id, [])
        values = [getattr(item, field_name, None) for item in history]
        values = [value for value in values if isinstance(value, (int, float))]
        if len(values) < 2:
            return None
        return float(values[-1] - values[0])

    def trend(self, cell_id: str) -> Optional[CellTrend]:
        history = self.get(cell_id)
        if not history:
            return None
        first, last = history[0], history[-1]
        age_delta = self.change(cell_id, "biological_age")
        abnormality_delta = self.change(cell_id, "abnormality")
        senescence_delta = self.change(cell_id, "senescence")
        confidence_values = [item.confidence for item in history if isinstance(item.confidence, (int, float))]
        confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
        if len(history) < 2:
            direction = "uncertain"
        elif abnormality_delta is not None and abnormality_delta >= 0.15:
            direction = "worsening"
        elif abnormality_delta is not None and abnormality_delta <= -0.15:
            direction = "improving"
        elif age_delta is not None and age_delta > 0:
            direction = "aging"
        else:
            direction = "stable"
        return CellTrend(cell_id, direction, age_delta, abnormality_delta, senescence_delta, confidence, len(history), "estimated" if len(history) >= 2 else "insufficient_evidence")

    def snapshot(self, cell_id: str) -> Dict[str, Any]:
        history = self.get(cell_id)
        return {"cell_id": cell_id, "observations": [state.to_dict() for state in history], "trend": self.trend(cell_id).to_dict() if history else None}

    def to_dict(self) -> Dict[str, Any]:
        return {
            cell_id: [state.to_dict() for state in history]
            for cell_id, history in self.states.items()
        }
