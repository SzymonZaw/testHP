"""Aggregate cell quality into tissue, region and hand summaries."""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .data_quality import Uncertainty
from .multiscale import ScaleAssessment


def aggregate_quality(assessments: Iterable[object]) -> Uncertainty:
    items = list(assessments)
    if not items:
        return Uncertainty(confidence=0.0, reason="no_assessments")
    confidence = sum(max(0.0, min(1.0, getattr(item, "confidence", 0.0))) for item in items) / len(items)
    return Uncertainty(confidence=confidence, reason="aggregated_from_children")


def enrich_scale_assessment(assessment: ScaleAssessment, children: Iterable[object]) -> ScaleAssessment:
    uncertainty = aggregate_quality(children)
    return replace(assessment, confidence=uncertainty.confidence, status=("estimated" if assessment.sufficient_cells else "insufficient_evidence"))
