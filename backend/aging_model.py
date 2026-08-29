from __future__ import annotations

"""Long-term aging model contract, without embedding an unvalidated aging clock."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgingTrajectory:
    spatial_id: str
    baseline_timepoint: str
    horizons: tuple[str, ...]
    states: tuple[dict[str, Any], ...]
    confidence: tuple[float | None, ...]
    model_id: str
    model_version: str
    assumptions: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.spatial_id or not self.baseline_timepoint or not self.model_id:
            raise ValueError("aging trajectory identity is required")
        if len(self.horizons) != len(self.states) or len(self.horizons) != len(self.confidence):
            raise ValueError("aging trajectory arrays must have equal length")
        if any(value is not None and not 0 <= value <= 1 for value in self.confidence):
            raise ValueError("aging confidence must be between 0 and 1")
