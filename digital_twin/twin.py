"""Main Digital Twin representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .tissue_state import TissueState
from .cell_state import CellState
from .biological_age import BiologicalAge
from .risk_state import RiskState
from .temporal_state import TemporalState
from .twin_update import TwinUpdater
from .spatial import HandSpatialModel
from .individual_cell import CellTimeline, IndividualCellState
from .cell_assessment import CellAssessment
from .hierarchical_assessment import aggregate_assessments
from .hierarchical_inference import aggregate_inference, HierarchicalInference
from .inference_intervention import InferenceAttention, build_inference_attention
from .assessment_trends import AssessmentTrend, compare_cell_assessments
from .intervention_map import InterventionItem, build_intervention_map
from .assessment_pipeline import build_assessment_view
from .observation import Observation
from .evidence import Evidence
from .cell_inference import CellInference, infer_cell
from .cell_inference_history import CellInferenceHistory, InferenceTrend


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
    observations: Dict[str, Observation] = field(default_factory=dict)
    evidence: Dict[str, Evidence] = field(default_factory=dict)
    inference_history: CellInferenceHistory = field(default_factory=CellInferenceHistory)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self) -> None:
        self.updater = TwinUpdater(self)

    def update(self, observation: Dict[str, Any], timepoint: Optional[str] = None) -> None:
        self.updater.update_from_observation(observation, timepoint=timepoint)
        self.updated_at = datetime.utcnow().isoformat()

    def add_observation(self, observation: Observation, confidence: Optional[float] = None) -> Evidence:
        """Register a raw observation and expose its traceable evidence."""
        if observation.subject_id != self.subject_id:
            raise ValueError("Observation subject_id must match the DigitalTwin subject_id")
        evidence = observation.to_evidence(confidence=confidence)
        self.observations[observation.observation_id] = observation
        self.evidence[observation.observation_id] = evidence
        self.metadata.setdefault("evidence_by_cell", {}).setdefault(observation.cell_id, []).append(observation.observation_id)
        self.updated_at = datetime.utcnow().isoformat()
        return evidence

    def get_cell_observations(self, cell_id: str) -> List[Observation]:
        return [item for item in self.observations.values() if item.cell_id == cell_id]

    def get_cell_evidence(self, cell_id: str) -> List[Evidence]:
        return [item for item in self.evidence.values() if self.observations.get(item.evidence_id) and self.observations[item.evidence_id].cell_id == cell_id]

    def infer_cell(self, cell_id: str, observed_at: Optional[datetime] = None) -> CellInference:
        """Infer and record the current conservative state of a cell."""
        inference = infer_cell(self.get_cell_evidence(cell_id))
        when = observed_at or max((item.observed_at for item in self.get_cell_observations(cell_id)), default=datetime.utcnow())
        self.inference_history.add(cell_id, when, inference)
        self.updated_at = datetime.utcnow().isoformat()
        return inference

    def cell_inference_history(self, cell_id: str) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in self.inference_history.get(cell_id)]

    def cell_inference_trend(self, cell_id: str) -> Optional[InferenceTrend]:
        return self.inference_history.trend(cell_id)

    def hierarchical_inference(self) -> Dict[str, Dict[str, HierarchicalInference]]:
        """Aggregate latest cell inferences through tissue, region and hand."""
        latest = {}
        trends = {}
        for cell_id, snapshots in self.inference_history._items.items():
            if snapshots:
                latest[cell_id] = snapshots[-1].inference
                if len(snapshots) > 1:
                    trends[cell_id] = self.inference_history.trend(cell_id)
        return aggregate_inference(self.spatial_model, latest, trends)

    def inference_attention_map(self) -> List[InferenceAttention]:
        """Rank hand hierarchy nodes for further observation, not treatment."""
        return build_inference_attention(self.hierarchical_inference())

    def add_cell_state(self, state: IndividualCellState) -> None:
        self.cell_timeline.add(state)
        self.updated_at = datetime.utcnow().isoformat()

    def assess_cell(self, state: IndividualCellState, assessment: CellAssessment) -> Optional[AssessmentTrend]:
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

    def assessment_view(self, cell_id: str, previous_assessment: Optional[CellAssessment] = None) -> Optional[Dict[str, Any]]:
        """Return the unified assessment payload used by API/UI consumers."""
        return build_assessment_view(self, cell_id, previous_assessment)

    def hierarchical_assessment(self) -> Dict[str, Dict[str, Any]]:
        aggregated = aggregate_assessments(self.spatial_model, self.cell_assessments)
        return {level: {identifier: assessment.to_dict() for identifier, assessment in groups.items()} for level, groups in aggregated.items()}

    def observation_priority_map(self, previous_assessments: Optional[Dict[str, CellAssessment]] = None) -> Dict[str, InterventionItem]:
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
        return self.cell_timeline.trend(cell_id)

    def cell_timeline_snapshot(self, cell_id: str) -> Dict[str, Any]:
        return self.cell_timeline.snapshot(cell_id)

    def cell_spatial_context(self, cell_id: str) -> Optional[Dict[str, Any]]:
        """Return the full hand -> region -> tissue context for a cell."""
        location = self.spatial_model.locate_cell(cell_id)
        if location is None:
            return None
        for region_id, region in self.spatial_model.regions.items():
            for tissue_id, tissue in region.tissues.items():
                if cell_id not in tissue.cells:
                    continue
                structure_id = location.structure_id
                structure = tissue.structures.get(structure_id) if structure_id else None
                return {
                    "hand": {"id": "hand", "level": "hand"},
                    "region": {"id": region_id, "level": "region", "name": region.name},
                    "tissue": {"id": tissue_id, "level": "tissue", "name": tissue.name or tissue.tissue_type},
                    "cell": {"id": cell_id, "level": "cell", "cell_type": location.cell_type},
                    "structure": {"id": structure_id, "level": "structure", "name": structure.name} if structure else None,
                }

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
            "observations": {observation_id: observation.to_dict() for observation_id, observation in self.observations.items()},
            "evidence": {evidence_id: evidence.to_dict() for evidence_id, evidence in self.evidence.items()},
            "inference_history": self.inference_history.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
