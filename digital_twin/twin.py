"""Main Digital Twin representation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .tissue_state import TissueState
from .cell_state import CellState
from .biological_age import BiologicalAge
from .risk_state import RiskState
from .temporal_state import TemporalState
from .twin_update import TwinUpdater
from .spatial import HandSpatialModel
from .individual_cell import CellTimeline, IndividualCellState
from .cell_aggregation import aggregate_cells


@dataclass
class DigitalTwin:
    """Central digital representation of a biological subject."""

    subject_id: str
    tissue_state: TissueState = field(default_factory=TissueState)
    cell_state: CellState = field(default_factory=CellState)
    biological_age: BiologicalAge = field(default_factory=BiologicalAge)
    risk_state: RiskState = field(default_factory=RiskState)
    temporal_state: TemporalState = field(default_factory=TemporalState)
    spatial_model: HandSpatialModel = field(default_factory=HandSpatialModel)
    cell_timeline: CellTimeline = field(default_factory=CellTimeline)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self) -> None:
        self.updater = TwinUpdater(self)

    def update(self, observation: Dict[str, Any], timepoint: Optional[str] = None) -> None:
        self.updater.update_from_observation(observation, timepoint=timepoint)
        self.updated_at = datetime.utcnow().isoformat()

    def add_cell_state(self, state: IndividualCellState) -> None:
        """Register an individual-cell observation in the longitudinal model."""
        self.cell_timeline.add(state)
        self.updated_at = datetime.utcnow().isoformat()

    def cell_state_history(self, cell_id: str):
        return self.cell_timeline.get(cell_id)

    def cell_state_change(self, cell_id: str, field_name: str):
        return self.cell_timeline.change(cell_id, field_name)

    def aggregate_cells(self) -> Dict[str, Any]:
        """Return the latest known state of each tracked cell and its aggregates."""
        states = [self.cell_timeline.latest(cell_id) for cell_id in self.cell_timeline.states]
        return aggregate_cells(state for state in states if state is not None)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "tissue_state": self.tissue_state.to_dict(),
            "cell_state": self.cell_state.to_dict(),
            "biological_age": self.biological_age.to_dict(),
            "risk_state": self.risk_state.to_dict(),
            "temporal_state": self.temporal_state.to_dict(),
            "spatial_model": self.spatial_model.to_dict(),
            "cell_timeline": self.cell_timeline.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def summary(self) -> Dict[str, Any]:
        cell_count = sum(len(tissue.cells) for region in self.spatial_model.regions.values() for tissue in region.tissues.values())
        return {
            "subject_id": self.subject_id,
            "biological_age": self.biological_age.biological_age,
            "age_acceleration": self.biological_age.age_acceleration,
            "overall_risk": self.risk_state.overall_risk,
            "risk_label": self.risk_state.risk_label,
            "tissue_abnormality": self.tissue_state.tissue_abnormality_score,
            "cellular_abnormality": self.cell_state.cellular_abnormality_score,
            "spatial_regions": len(self.spatial_model.regions),
            "spatial_cells": cell_count,
            "tracked_cells": len(self.cell_timeline.states),
            "timepoints": len(self.temporal_state.timepoints),
            "updated_at": self.updated_at,
        }

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.snapshot(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str | Path) -> "DigitalTwin":
        # Preserve the existing loader contract; individual-cell history is
        # restored separately when present in a snapshot.
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        twin = cls(subject_id=data["subject_id"])
        for raw in data.get("cell_timeline", {}).values():
            for item in raw:
                twin.add_cell_state(IndividualCellState(
                    cell_id=item["cell_id"],
                    observed_at=datetime.fromisoformat(item["observed_at"]),
                    morphology=item.get("morphology", {}),
                    biomarkers=item.get("biomarkers", {}),
                    proliferation=item.get("proliferation"),
                    senescence=item.get("senescence"),
                    apoptosis=item.get("apoptosis"),
                    abnormality=item.get("abnormality"),
                    biological_age=item.get("biological_age"),
                    confidence=item.get("confidence"),
                    metadata=item.get("metadata", {}),
                ))
        return twin
