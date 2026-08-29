"""Technology-neutral contracts for ML inference in the hand digital twin."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .data_foundation import Quality, SpatialReference, Uncertainty


@dataclass(frozen=True)
class ModelInput:
    """Validated model input derived from one or more observations."""

    sample_id: str
    modality: str
    features: Mapping[str, Any] = field(default_factory=dict)
    spatial_reference: SpatialReference | None = None
    quality: Quality = field(default_factory=Quality)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.sample_id:
            raise ValueError("sample_id is required")
        if not self.modality:
            raise ValueError("modality is required")
        if self.spatial_reference is not None:
            self.spatial_reference.validate()
        self.quality.validate()


@dataclass(frozen=True)
class ModelOutput:
    """Technology-neutral prediction returned by an ML model."""

    model_id: str
    model_version: str
    prediction: Any
    probabilities: Mapping[str, float] = field(default_factory=dict)
    confidence: float | None = None
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    attributions: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.model_id or not self.model_version:
            raise ValueError("model_id and model_version are required")
        for label, probability in self.probabilities.items():
            if not 0 <= probability <= 1:
                raise ValueError(f"probability for {label!r} must be between 0 and 1")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.uncertainty.validate()


class CellModel:
    """Minimal interface implemented by concrete ML inference adapters."""

    model_id: str = "unknown"
    model_version: str = "unknown"

    def predict(self, model_input: ModelInput) -> ModelOutput:
        raise NotImplementedError
