"""Stable contracts for future evidence-backed biological inference."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Status = Literal["not_established", "available"]
HealthState = Literal["healthy", "at_risk", "diseased", "unknown"]


@dataclass(frozen=True)
class BiologicalAgeResult:
    status: Status = "not_established"
    biological_age: float | None = None
    uncertainty: float | None = None
    model_id: str | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class HealthStateResult:
    state: HealthState = "unknown"
    confidence: float | None = None
    model_id: str | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class MolecularStateResult:
    modality: str
    status: Status = "not_established"
    features: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] | None = None
    confidence: float | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class MultimodalStateResult:
    status: Status = "not_established"
    state: dict[str, Any] | None = None
    confidence: float | None = None
    uncertainty: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class InterventionPriorityResult:
    status: Status = "not_established"
    priority: str | None = None
    confidence: float | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    clinical_validation: bool = False
