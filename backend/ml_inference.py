"""Registry-backed inference service for cell observations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cell_assessment_engine import CellAssessmentEngine
from .cell_observation import CellObservation
from .ml_adapters import model_output_to_cell_assessment, observation_to_model_input
from .ml_contracts import CellModel, ModelInput, ModelOutput
from .ml_registry import ModelRegistry


@dataclass(frozen=True)
class InferenceResult:
    """Auditable result containing both raw model output and domain assessment."""

    model_output: ModelOutput
    assessment: Any


class CellInferenceService:
    """Coordinates feature extraction, registry lookup, inference and adaptation."""

    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def predict_input(
        self,
        observation: CellObservation,
        model_input: ModelInput,
        *,
        model_id: str,
        model_version: str | None = None,
    ) -> InferenceResult:
        """Infer from a prepared ModelInput while retaining observation provenance."""
        observation.validate()
        model_input.validate()
        model: CellModel = self.registry.get(model_id, model_version)
        output = model.predict(model_input)
        output.validate()
        assessment = model_output_to_cell_assessment(observation, output)
        return InferenceResult(model_output=output, assessment=assessment)

    def predict(
        self,
        observation: CellObservation,
        *,
        model_id: str,
        model_version: str | None = None,
    ) -> InferenceResult:
        """Build the default model input directly from an observation and infer."""
        model_input = observation_to_model_input(observation)
        return self.predict_input(
            observation,
            model_input,
            model_id=model_id,
            model_version=model_version,
        )

    def predict_with_baseline(self, observation: CellObservation) -> InferenceResult:
        """Run the deterministic assessment while ML deployment is unavailable."""
        result = CellAssessmentEngine().assess(observation)
        output = ModelOutput(
            model_id="deterministic-cell-baseline",
            model_version="0.1.0",
            prediction=result.assessment.state,
            confidence=result.assessment.confidence,
            metadata={"signals": result.signals},
        )
        return InferenceResult(model_output=output, assessment=result.assessment)
