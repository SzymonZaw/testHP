"""Multiscale aggregation for hand -> region -> tissue -> cell assessments.

This module summarizes observed/modelled data and explicitly preserves coverage
and confidence. It is not a clinical diagnosis or treatment engine.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class ScaleAssessment:
    level: str
    target_id: str
    assessed_cells: int
    sufficient_cells: int
    coverage: float
    biological_age: Optional[float]
    confidence: float
    status: str

    def to_dict(self):
        return asdict(self)


def aggregate_cell_assessments(
    target_id: str,
    level: str,
    assessments: Iterable[object],
) -> ScaleAssessment:
    items = list(assessments)
    assessed = len(items)
    usable = [item for item in items if getattr(item, "biological_age", None) is not None]
    sufficient = len(usable)
    coverage = sufficient / assessed if assessed else 0.0
    if usable:
        weights = [max(0.0, min(1.0, getattr(item, "confidence", 0.0))) for item in usable]
        total = sum(weights)
        age = sum(item.biological_age * weight for item, weight in zip(usable, weights)) / total if total else None
        confidence = total / len(weights) if weights else 0.0
    else:
        age = None
        confidence = 0.0
    status = "estimated" if sufficient else "insufficient_evidence"
    return ScaleAssessment(level, target_id, assessed, sufficient, coverage, age, confidence, status)
