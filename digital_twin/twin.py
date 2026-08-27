"""
Main Digital Twin representation.

The DigitalTwin class combines biological state with a spatial hierarchy
that can represent the hand from anatomical regions down to individual cells.
"""

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

    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def __post_init__(self) -> None:
        self.updater = TwinUpdater(self)

    def update(
        self,
        observation: Dict[str, Any],
        timepoint: Optional[str] = None,
    ) -> None:
        """Update the digital twin from a new observation."""
        self.updater.update_from_observation(observation, timepoint=timepoint)
        self.updated_at = datetime.utcnow().isoformat()

    def snapshot(self) -> Dict[str, Any]:
        """Return the complete current twin state."""
        return {
            "subject_id": self.subject_id,
            "tissue_state": self.tissue_state.to_dict(),
            "cell_state": self.cell_state.to_dict(),
            "biological_age": self.biological_age.to_dict(),
            "risk_state": self.risk_state.to_dict(),
            "temporal_state": self.temporal_state.to_dict(),
            "spatial_model": self.spatial_model.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def summary(self) -> Dict[str, Any]:
        """Return a compact summary of the biological state."""
        cell_count = sum(
            len(tissue.cells)
            for region in self.spatial_model.regions.values()
            for tissue in region.tissues.values()
        )
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
            "timepoints": len(self.temporal_state.timepoints),
            "updated_at": self.updated_at,
        }

    def save(self, path: str | Path) -> None:
        """Save digital twin to JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.snapshot(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str | Path) -> "DigitalTwin":
        """Load a DigitalTwin from JSON."""
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        spatial_data = data.get("spatial_model", {})
        spatial_model = HandSpatialModel()
        spatial_model.coordinate_system = spatial_data.get(
            "coordinate_system", "hand"
        )
        spatial_model.metadata = spatial_data.get("metadata", {})
        spatial_model.updated_at = spatial_data.get(
            "updated_at", datetime.utcnow().isoformat()
        )

        # Reconstruct the spatial hierarchy without requiring a schema migration
        # for older snapshots that did not contain spatial_model.
        from .spatial import CellLocation, HandRegion, SpatialPoint, StructureRegion, TissueRegion

        for region_id, raw_region in spatial_data.get("regions", {}).items():
            region = HandRegion(
                region_id=raw_region["region_id"],
                name=raw_region["name"],
                side=raw_region.get("side"),
                bounds_min=(SpatialPoint(**raw_region["bounds_min"])
                            if raw_region.get("bounds_min") else None),
                bounds_max=(SpatialPoint(**raw_region["bounds_max"])
                            if raw_region.get("bounds_max") else None),
                metadata=raw_region.get("metadata", {}),
            )
            for tissue_id, raw_tissue in raw_region.get("tissues", {}).items():
                tissue = TissueRegion(
                    tissue_id=raw_tissue["tissue_id"],
                    tissue_type=raw_tissue.get("tissue_type", "skin"),
                    name=raw_tissue.get("name"),
                    region_id=raw_tissue.get("region_id"),
                    bounds_min=(SpatialPoint(**raw_tissue["bounds_min"])
                                if raw_tissue.get("bounds_min") else None),
                    bounds_max=(SpatialPoint(**raw_tissue["bounds_max"])
                                if raw_tissue.get("bounds_max") else None),
                    metadata=raw_tissue.get("metadata", {}),
                )
                for structure_id, raw_structure in raw_tissue.get("structures", {}).items():
                    tissue.add_structure(StructureRegion(
                        structure_id=raw_structure["structure_id"],
                        name=raw_structure["name"],
                        region_id=raw_structure.get("region_id"),
                        structure_type=raw_structure.get("structure_type"),
                        bounds_min=(SpatialPoint(**raw_structure["bounds_min"])
                                    if raw_structure.get("bounds_min") else None),
                        bounds_max=(SpatialPoint(**raw_structure["bounds_max"])
                                    if raw_structure.get("bounds_max") else None),
                        metadata=raw_structure.get("metadata", {}),
                    ))
                for cell_id, raw_cell in raw_tissue.get("cells", {}).items():
                    tissue.add_cell(CellLocation(
                        cell_id=raw_cell["cell_id"],
                        position=SpatialPoint(**raw_cell["position"]),
                        tissue_id=raw_cell.get("tissue_id"),
                        structure_id=raw_cell.get("structure_id"),
                        cell_type=raw_cell.get("cell_type"),
                        confidence=raw_cell.get("confidence", 0.0),
                        metadata=raw_cell.get("metadata", {}),
                    ))
                region.add_tissue(tissue)
            spatial_model.add_region(region)

        return cls(
            subject_id=data["subject_id"],
            tissue_state=TissueState.from_dict(data["tissue_state"]),
            cell_state=CellState.from_dict(data["cell_state"]),
            biological_age=BiologicalAge.from_dict(data["biological_age"]),
            risk_state=RiskState.from_dict(data["risk_state"]),
            temporal_state=TemporalState.from_dict(data["temporal_state"]),
            spatial_model=spatial_model,
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )
