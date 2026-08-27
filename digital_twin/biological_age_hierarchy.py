"""Hierarchical aggregation of research-only biological age estimates.

Aggregates Cell -> Tissue -> Region -> Hand while preserving uncertainty,
confidence and evidence coverage. This is not a clinical model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .biological_age_v01 import BiologicalAgeEstimate


@dataclass(frozen=True)
class HierarchicalAgeEstimate:
    level: str
    identifier: str
    overall_age: Optional[float]
    confidence: float
    evidence_count: int
    assessed_items: int
    sufficient_items: int
    status: str


def aggregate_age_estimates(
    estimates: Iterable[BiologicalAgeEstimate],
    *,
    level: str,
    identifier: str,
    minimum_sufficient_items: int = 1,
) -> HierarchicalAgeEstimate:
    """Aggregate child estimates using confidence as the weight.

    Items without an overall estimate remain part of coverage counts but never
    contribute an invented age value.
    """
    items = list(estimates)
    sufficient = [item for item in items if item.overall_age is not None and item.confidence > 0]
    evidence_count = sum(item.evidence_count for item in sufficient)
    if len(sufficient) < minimum_sufficient_items:
        confidence = (sum(item.confidence for item in sufficient) / len(sufficient)) if sufficient else 0.0
        return HierarchicalAgeEstimate(
            level, identifier, None, confidence, evidence_count,
            len(items), len(sufficient), "insufficient_evidence",
        )

    total_weight = sum(item.confidence for item in sufficient)
    overall_age = sum(item.overall_age * item.confidence for item in sufficient) / total_weight
    confidence = total_weight / len(sufficient)
    return HierarchicalAgeEstimate(
        level, identifier, overall_age, confidence, evidence_count,
        len(items), len(sufficient), "estimated",
    )
