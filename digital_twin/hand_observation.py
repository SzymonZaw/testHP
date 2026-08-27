"""Immutable longitudinal observations of a hand digital twin."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from .cell_profile import CellProfile
from .hand_state import HandState
from .region_state import RegionState
from .tissue_state import TissueState


@dataclass(frozen=True)
class HandObservation:
    """Point-in-time snapshot; later observations do not mutate it."""

    observation_id: str
    observed_at: str
    hand_id: str
    cells: Mapping[str, CellProfile] = field(default_factory=dict)
    tissues: Mapping[str, TissueState] = field(default_factory=dict)
    regions: Mapping[str, RegionState] = field(default_factory=dict)
    hand_state: Optional[HandState] = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))
        object.__setattr__(self, "cells", dict(self.cells))
        object.__setattr__(self, "tissues", dict(self.tissues))
        object.__setattr__(self, "regions", dict(self.regions))
        object.__setattr__(self, "provenance", dict(self.provenance))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "observed_at": self.observed_at,
            "hand_id": self.hand_id,
            "cells": {key: value.to_dict() for key, value in self.cells.items()},
            "tissues": {key: value.to_dict() for key, value in self.tissues.items()},
            "regions": {key: value.to_dict() for key, value in self.regions.items()},
            "hand_state": self.hand_state.to_dict() if self.hand_state else None,
            "provenance": dict(self.provenance),
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }
