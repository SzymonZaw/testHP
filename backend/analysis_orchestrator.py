"""Canonical end-user analysis orchestration boundary.

This module defines the order of operations without inventing biological
predictions. Domain-specific analyzers can be injected as callables. Missing
or unvalidated model output remains explicitly ``not_established``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from .biological_models import (
    BiologicalAgeResult,
    HealthStateResult,
    InterventionPriorityResult,
    MolecularStateResult,
    MultimodalStateResult,
)


@dataclass(frozen=True)
class Provenance:
    input_id: str
    analysis_id: str
    model_id: str | None = None
    model_version: str | None = None
    dataset_version: str | None = None
    pipeline_version: str = "1"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "end_user"


@dataclass(frozen=True)
class QCResult:
    modality: str
    status: str  # missing | unusable | usable
    reasons: tuple[str, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisResult:
    provenance: Provenance
    validation: dict[str, Any]
    qc: tuple[QCResult, ...]
    features: dict[str, Any]
    biological_age: BiologicalAgeResult
    health_state: HealthStateResult
    molecular_states: tuple[MolecularStateResult, ...]
    multimodal_state: MultimodalStateResult
    intervention_priority: InterventionPriorityResult


class AnalysisOrchestrator:
    """One official pipeline from user input to a Digital Twin result."""

    def __init__(self, *, input_validator: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
                 modality_analyzer: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
                 feature_extractor: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
                 biological_model: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
                 fusion_model: Callable[[dict[str, Any]], MultimodalStateResult] | None = None) -> None:
        self.input_validator = input_validator
        self.modality_analyzer = modality_analyzer
        self.feature_extractor = feature_extractor
        self.biological_model = biological_model
        self.fusion_model = fusion_model

    def run(self, user_input: dict[str, Any], *, input_id: str | None = None,
            source: str = "end_user") -> AnalysisResult:
        input_id = input_id or str(uuid4())
        analysis_id = str(uuid4())
        validation = self.input_validator(user_input) if self.input_validator else {"valid": True}
        if validation.get("valid") is False:
            raise ValueError("user input validation failed")

        analyzed = self.modality_analyzer(user_input) if self.modality_analyzer else dict(user_input)
        qc = tuple(self._qc(analyzed))
        usable = {k: v for k, v in analyzed.items() if k not in {"_qc"}}
        features = self.feature_extractor(usable) if self.feature_extractor else {}
        biological = self.biological_model(features) if self.biological_model else {}
        age = biological.get("biological_age", BiologicalAgeResult())
        health = biological.get("health_state", HealthStateResult())
        molecular = tuple(biological.get("molecular_states", ()))
        fusion = self.fusion_model(features) if self.fusion_model else MultimodalStateResult()
        intervention = biological.get("intervention_priority", InterventionPriorityResult())

        model = biological.get("model", {}) if isinstance(biological, dict) else {}
        provenance = Provenance(
            input_id=input_id,
            analysis_id=analysis_id,
            model_id=model.get("model_id"),
            model_version=model.get("model_version"),
            dataset_version=model.get("dataset_version"),
            pipeline_version=model.get("pipeline_version", "1"),
            source=source,
        )
        return AnalysisResult(provenance, validation, qc, features, age, health, molecular, fusion, intervention)

    @staticmethod
    def _qc(data: dict[str, Any]) -> list[QCResult]:
        modalities = ("hand_images", "hand_video", "hand_3d", "tissue_wsi", "rna", "proteomics", "epigenetics", "genomics")
        results = []
        for modality in modalities:
            value = data.get(modality)
            if value is None:
                results.append(QCResult(modality, "missing"))
            elif isinstance(value, dict) and value.get("qc_status") == "unusable":
                results.append(QCResult(modality, "unusable", tuple(value.get("reasons", ()))))
            else:
                results.append(QCResult(modality, "usable"))
        return results
