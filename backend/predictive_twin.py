from __future__ import annotations

"""Predictive, provenance-aware twin primitives."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Prediction:
    spatial_id: str
    horizon: str
    predicted_state: dict[str, Any]
    confidence: float | None
    model_id: str
    model_version: str
    evidence_ids: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.spatial_id or not self.horizon or not self.model_id or not self.model_version:
            raise ValueError("prediction provenance is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("prediction confidence must be between 0 and 1")


def build_prediction(**kwargs: Any) -> Prediction:
    result = Prediction(**kwargs)
    result.validate()
    return result
