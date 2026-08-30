"""Safe inference boundary.

Until validated models are registered, every biological inference remains
explicitly unestablished. This prevents missing model/data coverage from being
mistaken for a positive biological finding.
"""
from __future__ import annotations

from .contracts import (
    BiologicalAgeResult,
    HealthStateResult,
    InterventionPriorityResult,
    MolecularStateResult,
    MultimodalStateResult,
)


def biological_age(*, level: str, features: dict | None = None) -> BiologicalAgeResult:
    return BiologicalAgeResult()


def health_state(*, level: str, features: dict | None = None) -> HealthStateResult:
    return HealthStateResult()


def molecular_state(*, modality: str, features: dict | None = None) -> MolecularStateResult:
    return MolecularStateResult(modality=modality)


def multimodal_state(*, features: dict | None = None) -> MultimodalStateResult:
    return MultimodalStateResult()


def intervention_priority(*, features: dict | None = None) -> InterventionPriorityResult:
    return InterventionPriorityResult()
