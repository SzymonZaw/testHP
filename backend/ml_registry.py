"""Versioned registry for ML models used by the hand digital twin."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .ml_contracts import CellModel


@dataclass(frozen=True)
class ModelSpec:
    """Immutable metadata describing a deployable model version."""

    model_id: str
    model_version: str
    task: str
    modalities: tuple[str, ...] = ()
    artifact_uri: str | None = None
    checksum: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.model_id or not self.model_version or not self.task:
            raise ValueError("model_id, model_version, and task are required")
        if not self.modalities:
            raise ValueError("at least one modality is required")


class ModelRegistry:
    """In-process registry; storage can later be backed by a model registry service."""

    def __init__(self) -> None:
        self._models: dict[tuple[str, str], tuple[ModelSpec, CellModel]] = {}

    def register(self, spec: ModelSpec, model: CellModel) -> None:
        spec.validate()
        if model.model_id != spec.model_id or model.model_version != spec.model_version:
            raise ValueError("model metadata does not match implementation")
        key = (spec.model_id, spec.model_version)
        if key in self._models:
            raise ValueError(f"model version already registered: {spec.model_id}@{spec.model_version}")
        self._models[key] = (spec, model)

    def get(self, model_id: str, model_version: str | None = None) -> CellModel:
        if model_version is None:
            versions = [key for key in self._models if key[0] == model_id]
            if not versions:
                raise KeyError(model_id)
            key = max(versions, key=lambda item: item[1])
        else:
            key = (model_id, model_version)
        try:
            return self._models[key][1]
        except KeyError as exc:
            raise KeyError(f"model not registered: {key[0]}@{key[1]}") from exc

    def spec(self, model_id: str, model_version: str | None = None) -> ModelSpec:
        model = self.get(model_id, model_version)
        return self._models[(model.model_id, model.model_version)][0]
