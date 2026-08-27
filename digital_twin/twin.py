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

    def add_cell_assessment(self, assessment: CellAssessment) -> None:
        """Store the latest evidence-aware assessment for a cell."""
        if assessment.cell_id not in self.cell_timeline.states:
            raise KeyError(f"Cannot assess untracked cell: {assessment.cell_id}")
        self.cell_assessments[assessment.cell_id] = assessment
        self.updated_at = datetime.utcnow().isoformat()

    def get_cell_assessment(self, cell_id: str) -> Optional[CellAssessment]:
        return self.cell_assessments.get(cell_id)

    def cell_state_history(self, cell_id: str):
        return self.cell_timeline.get(cell_id)

    def cell_state_change(self, cell_id: str, field_name: str):
        return self.cell_timeline.change(cell_id, field_name)

    def aggregate_cells(self) -> Dict[str, Any]:
        states = [self.cell_timeline.latest(cell_id) for cell_id in self.cell_timeline.states]
        return aggregate_cells(state for state in states if state is not None)

    def snapshot(self) -> Dict[str, Any]:
        """Return a lossless, JSON-serializable representation of the twin."""
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
            "assessed_cells": len(self.cell_assessments),
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
        """Load all current twin layers from a snapshot."""
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        spatial_model = cls._load_spatial_model(data.get("spatial_model", {}))
        timeline = cls._load_cell_timeline(data.get("cell_timeline", {}))
        assessments = {
            cell_id: CellAssessment.from_dict(raw)
            for cell_id, raw in data.get("cell_assessments", {}).items()
        }

        return cls(
            subject_id=data["subject_id"],
            tissue_state=TissueState.from_dict(data.get("tissue_state", {})),
            cell_state=CellState.from_dict(data.get("cell_state", {})),
            biological_age=BiologicalAge.from_dict(data.get("biological_age", {})),
            risk_state=RiskState.from_dict(data.get("risk_state", {})),
            temporal_state=TemporalState.from_dict(data.get("temporal_state", {})),
            spatial_model=spatial_model,
            cell_timeline=timeline,
            cell_assessments=assessments,
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )

    @staticmethod
    def _point(data: Optional[Dict[str, Any]]) -> Optional[SpatialPoint]:
        if data is None:
            return None
        return SpatialPoint(x=data["x"], y=data["y"], z=data["z"], coordinate_system=data.get("coordinate_system", "hand"))

    @classmethod
    def _load_spatial_model(cls, data: Dict[str, Any]) -> HandSpatialModel:
        model = HandSpatialModel(
            coordinate_system=data.get("coordinate_system", "hand"),
            metadata=data.get("metadata", {}),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )
        for region_id, raw_region in data.get("regions", {}).items():
            region = HandRegion(
                region_id=raw_region.get("region_id", region_id), name=raw_region.get("name", region_id),
                side=raw_region.get("side"), bounds_min=cls._point(raw_region.get("bounds_min")),
                bounds_max=cls._point(raw_region.get("bounds_max")), metadata=raw_region.get("metadata", {}),
            )
            for tissue_id, raw_tissue in raw_region.get("tissues", {}).items():
                tissue = TissueRegion(
                    tissue_id=raw_tissue.get("tissue_id", tissue_id), tissue_type=raw_tissue.get("tissue_type", "skin"),
                    name=raw_tissue.get("name"), region_id=raw_tissue.get("region_id"),
                    bounds_min=cls._point(raw_tissue.get("bounds_min")), bounds_max=cls._point(raw_tissue.get("bounds_max")),
                    metadata=raw_tissue.get("metadata", {}),
                )
                for structure_id, raw_structure in raw_tissue.get("structures", {}).items():
                    tissue.add_structure(StructureRegion(
                        structure_id=raw_structure.get("structure_id", structure_id), name=raw_structure.get("name", structure_id),
                        region_id=raw_structure.get("region_id"), structure_type=raw_structure.get("structure_type"),
                        bounds_min=cls._point(raw_structure.get("bounds_min")), bounds_max=cls._point(raw_structure.get("bounds_max")),
                        metadata=raw_structure.get("metadata", {}),
                    ))
                for cell_id, raw_cell in raw_tissue.get("cells", {}).items():
                    position = cls._point(raw_cell.get("position"))
                    if position is None:
                        raise ValueError(f"Cell '{cell_id}' is missing position")
                    tissue.add_cell(CellLocation(
                        cell_id=raw_cell.get("cell_id", cell_id), position=position,
                        tissue_id=raw_cell.get("tissue_id"), structure_id=raw_cell.get("structure_id"),
                        cell_type=raw_cell.get("cell_type"), confidence=raw_cell.get("confidence", 0.0),
                        metadata=raw_cell.get("metadata", {}),
                    ))
                region.add_tissue(tissue)
            model.add_region(region)
        return model

    @staticmethod
    def _load_cell_timeline(data: Dict[str, Any]) -> CellTimeline:
        timeline = CellTimeline()
        for cell_id, history in data.items():
            for item in history:
                timeline.add(IndividualCellState(
                    cell_id=item.get("cell_id", cell_id), observed_at=datetime.fromisoformat(item["observed_at"]),
                    morphology=item.get("morphology", {}), biomarkers=item.get("biomarkers", {}),
                    proliferation=item.get("proliferation"), senescence=item.get("senescence"),
                    apoptosis=item.get("apoptosis"), abnormality=item.get("abnormality"),
                    biological_age=item.get("biological_age"), confidence=item.get("confidence"),
                    metadata=item.get("metadata", {}),
                ))
        return timeline
