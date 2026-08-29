"""Transparent prioritization of regional aging observations.

This module produces a research/observation priority signal only. It is not a
clinical diagnosis, treatment recommendation, or medical triage mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .aging_outliers import AgingOutlier


@dataclass(frozen=True)
class AgingPriority:
    level: str
    node_id: str
    priority_score: float | None
    priority: str
    reason_codes: tuple[str, ...]
    confidence: float | None
    uncertainty: float | None
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "node_id": self.node_id,
            "priority_score": self.priority_score,
            "priority": self.priority,
            "reason_codes": self.reason_codes,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
        }


def prioritize_aging_outlier(
    outlier: AgingOutlier,
    *,
    low_threshold: float = 0.25,
    high_threshold: float = 0.75,
) -> AgingPriority:
    """Convert an analytical outlier into an observation priority signal.

    The score is normalized against the supplied thresholds and capped at 1.
    Confidence and uncertainty are propagated unchanged; no clinical action is
    inferred from the score.
    """
    if low_threshold < 0 or high_threshold <= low_threshold:
        raise ValueError("thresholds must satisfy 0 <= low_threshold < high_threshold")

    provenance = tuple(sorted(set(outlier.provenance) | {"aging_priority"}))
    if outlier.outlier_score is None:
        return AgingPriority(outlier.level, outlier.node_id, None, "insufficient_data",
                             ("missing_outlier_score",), outlier.confidence,
                             outlier.uncertainty, outlier.evidence_ids, provenance)

    score = max(0.0, min(1.0, (float(outlier.outlier_score) - low_threshold) /
                           (high_threshold - low_threshold)))
    reasons = [outlier.direction]
    if outlier.uncertainty is not None:
        reasons.append("uncertainty_available")
    if outlier.confidence is not None and outlier.confidence < 0.5:
        reasons.append("low_confidence")

    if score >= 1.0 and (outlier.confidence is None or outlier.confidence >= 0.5):
        priority = "high"
    elif score > 0.0:
        priority = "medium"
    else:
        priority = "low"

    return AgingPriority(outlier.level, outlier.node_id, score, priority,
                         tuple(sorted(set(reasons))), outlier.confidence,
                         outlier.uncertainty, outlier.evidence_ids, provenance)


def prioritize_aging_outliers(
    outliers: Iterable[AgingOutlier],
    *,
    low_threshold: float = 0.25,
    high_threshold: float = 0.75,
) -> tuple[AgingPriority, ...]:
    """Prioritize multiple regional signals deterministically."""
    results = tuple(
        prioritize_aging_outlier(item, low_threshold=low_threshold, high_threshold=high_threshold)
        for item in outliers
    )
    return tuple(sorted(results, key=lambda item: (-(item.priority_score or -1.0), item.node_id)))
