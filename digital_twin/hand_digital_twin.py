"""Hierarchical container for the hand digital twin."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .cell_profile import CellProfile
from .hand_observation import HandObservation
from .tissue_state import TissueState
from .region_state import RegionState
from .hand_state import HandState, aggregate_hand_state


@dataclass
class HandDigitalTwin:
    """Canonical hierarchical representation of one hand."""

    hand_id: str
    cells: Dict[str, CellProfile] = field(default_factory=dict)
    tissues: Dict[str, TissueState] = field(default_factory=dict)
    regions: Dict[str, RegionState] = field(default_factory=dict)
    state: Optional[HandState] = None
    observations: List[HandObservation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_cell(self, cell: CellProfile) -> None:
        self.cells[cell.cell_id] = cell

    def add_tissue(self, tissue_id: str, tissue: TissueState) -> None:
        self.tissues[tissue_id] = tissue

    def add_region(self, region: RegionState) -> None:
        self.regions[region.region_id] = region

    def cells_for_tissue(self, tissue_id: str) -> List[CellProfile]:
        return [c for c in self.cells.values() if c.tissue_id == tissue_id]

    def aggregate_tissue(self, tissue_id: str, *, confidence: Optional[float] = None) -> TissueState:
        tissue = self.tissues.get(tissue_id, TissueState(tissue_type=tissue_id))
        tissue.aggregate_cells(self.cells_for_tissue(tissue_id), confidence=confidence)
        self.tissues[tissue_id] = tissue
        return tissue

    def aggregate_hand(self, *, confidence: Optional[float] = None) -> Optional[HandState]:
        if not self.regions:
            self.state = None
            return None
        self.state = aggregate_hand_state(self.hand_id, self.regions.values(), confidence=confidence)
        return self.state

    def record_observation(
        self,
        observation_id: str,
        observed_at: str,
        *,
        provenance: Optional[Dict[str, Any]] = None,
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> HandObservation:
        """Capture the current state without changing previous observations."""
        observation = HandObservation(
            observation_id=observation_id,
            observed_at=observed_at,
            hand_id=self.hand_id,
            cells=self.cells,
            tissues=self.tissues,
            regions=self.regions,
            hand_state=self.state,
            provenance=provenance or {},
            confidence=confidence,
            metadata=metadata or {},
        )
        self.observations.append(observation)
        return observation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hand_id": self.hand_id,
            "cells": {key: value.to_dict() for key, value in self.cells.items()},
            "tissues": {key: value.to_dict() for key, value in self.tissues.items()},
            "regions": {key: value.to_dict() for key, value in self.regions.items()},
            "state": self.state.to_dict() if self.state else None,
            "observations": [observation.to_dict() for observation in self.observations],
            "metadata": dict(self.metadata),
        }
