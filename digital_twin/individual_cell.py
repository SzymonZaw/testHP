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

    def to_dict(self) -> Dict[str, Any]:
        return {
            cell_id: [state.to_dict() for state in history]
            for cell_id, history in self.states.items()
        }
