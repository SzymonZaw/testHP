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
from .spatial import CellLocation, HandRegion, HandSpatialModel, SpatialPoint, StructureRegion, TissueRegion
from .individual_cell import CellTimeline, IndividualCellState
from .cell_aggregation import aggregate_cells
from .cell_assessment import CellAssessment
from .hierarchical_assessment import aggregate_assessments
from .assessment_trends import AssessmentTrend, compare_cell_assessments
from .intervention_map import InterventionItem, build_intervention_map


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
    cell_assessments: Dict[str, CellAssessment] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self) -> None:
        self.updater = TwinUpdater(self)

    def update(self, observation: Dict[str, Any], timepoint: Optional[str] = None) -> None:
        self.updater.update_from_observation(observation, timepoint=timepoint)
        self.updated_at = datetime.utcnow().isoformat()

    def add_cell_state(self, state: IndividualCellState) -> None:
        self.cell_timeline.add(state)
        self.updated_at = datetime.utcnow().isoformat()

    def assess_cell(self, state: IndividualCellState, assessment: CellAssessment) -> Optional[AssessmentTrend]:
        """Record a cell state and assessment, returning its longitudinal trend."""
        if state.cell_id != assessment.cell_id:
            raise ValueError("Cell state and assessment must reference the same cell")
        self.add_cell_state(state)
        previous = self.cell_assessments.get(assessment.cell_id)
        self.add_cell_assessment(assessment)
        return compare_cell_assessments(previous, assessment) if previous else None

    def add_cell_assessment(self, assessment: CellAssessment) -> None:
        if assessment.cell_id not in self.cell_timeline.states:
            raise KeyError(f"Cannot assess untracked cell: {assessment.cell_id}")
        self.cell_assessments[assessment.cell_id] = assessment
        self.updated_at = datetime.utcnow().isoformat()

    def get_cell_assessment(self, cell_id: str) -> Optional[CellAssessment]:
        return self.cell_assessments.get(cell_id)

    def hierarchical_assessment(self) -> Dict[str, Dict[str, Any]]:
        aggregated = aggregate_assessments(self.spatial_model, self.cell_assessments)
        return {level: {identifier: assessment.to_dict() for identifier, assessment in groups.items()} for level, groups in aggregated.items()}

    def observation_priority_map(self, previous_assessments: Optional[Dict[str, CellAssessment]] = None) -> Dict[str, InterventionItem]:
        """Build transparent observation priorities from current and optional prior assessments."""
        trends: Dict[str, AssessmentTrend] = {}
        if previous_assessments:
            for cell_id, current in self.cell_assessments.items():
                previous = previous_assessments.get(cell_id)
                if previous:
                    trends[cell_id] = compare_cell_assessments(previous, current)
        return build_intervention_map(self.cell_assessments, trends)

    def cell_state_history(self, cell_id: str):
        return self.cell_timeline.get(cell_id)

    def cell_state_change(self, cell_id: str, field_name: str):
        return self.cell_timeline.change(cell_id, field_name)

    def cell_trend(self, cell_id: str):
        """Return the longitudinal trend for one tracked cell."""
        return self.cell_timeline.trend(cell_id)

    def cell_timeline_snapshot(self, cell_id: str) -> Dict[str, Any]:
        """Return observations and derived trend for frontend/API consumers."""
        return self.cell_timeline.snapshot(cell_id)

    def aggregate_cells(self) -> Dict[str, Any]:
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
            "cell_assessments": {cell_id: assessment.to_dict() for cell_id, assessment in self.cell_assessments.items()},
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }