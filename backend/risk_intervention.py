from __future__ import annotations

"""Evidence-backed risk and intervention maps.

These are decision-support data structures only; they do not prescribe medical
care and require explicit evidence/model provenance for derived scores.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

RiskLevel = Literal["normal", "monitor", "elevated", "high", "unknown"]
ActionLevel = Literal["observe", "investigate", "treat", "regenerate", "none", "unknown"]


@dataclass(frozen=True)
class RiskMapEntry:
    spatial_id: str
    level: RiskLevel
    score: float | None
    confidence: float | None
    rationale: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    model_id: str | None = None
    model_version: str | None = None


@dataclass(frozen=True)
class InterventionMapEntry:
    spatial_id: str
    action: ActionLevel
    priority: float | None
    confidence: float | None
    rationale: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()


def validate_probability(value: float | None, name: str) -> None:
    if value is not None and not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")


def validate_risk(entry: RiskMapEntry) -> None:
    if not entry.spatial_id:
        raise ValueError("risk map requires spatial_id")
    validate_probability(entry.score, "score")
    validate_probability(entry.confidence, "confidence")


def validate_intervention(entry: InterventionMapEntry) -> None:
    if not entry.spatial_id:
        raise ValueError("intervention map requires spatial_id")
    validate_probability(entry.priority, "priority")
    validate_probability(entry.confidence, "confidence")
