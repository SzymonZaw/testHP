"""Registry for evidence-backed model metadata.

This registry intentionally does not contain predictive models yet. A model is
only eligible for production inference after its validation metadata is
registered explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelMetadata:
    model_id: str
    version: str
    task: str
    input_modalities: tuple[str, ...]
    target_level: str
    tissue_scope: tuple[str, ...] = ()
    cell_type_scope: tuple[str, ...] = ()
    training_dataset: str | None = None
    validation_dataset: str | None = None
    performance: dict[str, Any] = field(default_factory=dict)
    validation_status: str = "not_validated"


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModelMetadata] = {}

    def register(self, metadata: ModelMetadata) -> None:
        self._models[metadata.model_id] = metadata

    def get(self, model_id: str) -> ModelMetadata | None:
        return self._models.get(model_id)

    def production_ready(self, model_id: str) -> bool:
        model = self.get(model_id)
        return model is not None and model.validation_status == "validated"

    def all(self) -> list[ModelMetadata]:
        return list(self._models.values())


registry = ModelRegistry()
