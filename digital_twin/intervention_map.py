"""Observation-priority mapping for the digital twin.

This module deliberately does not recommend treatment. It converts measured
state, trend and uncertainty into transparent monitoring priorities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .assessment_trends import AssessmentTrend
from .cell_assessment import CellAssessment


@dataclass
class InterventionItem:
    identifier: str
    priority: str
    reason: str
    abnormality_score: Optional[float] = None
    trend_abnormality_delta: Optional[float] = None
    uncertainty: Optional[float] = None
    evidence_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def classify_priority(
    assessment: CellAssessment,
    trend: Optional[AssessmentTrend] = None,
    *,
    abnormality_threshold: float = 0.6,
    worsening_threshold: float = 0.1,
    high_uncertainty: float = 0.4,
) -> InterventionItem:
    """Classify observation priority using explicit, non-clinical rules."""
    abnormality = assessment.abnormality_score
    delta = trend.abnormality_delta if trend else None
    uncertainty = assessment.uncertainty

    if abnormality is None:
        priority = "monitor"
        reason = "insufficient_abnormality_data"
    elif abnormality >= abnormality_threshold and (delta is None or delta >= worsening_threshold):
        priority = "investigate"
        reason = "high_or_worsening_abnormality"
    elif delta is not None and delta >= worsening_threshold:
        priority = "monitor_closely"
        reason = "worsening_trend"
    elif uncertainty is not None and uncertainty >= high_uncertainty:
        priority = "improve_measurement"
        reason = "high_uncertainty"
    else:
        priority = "no_action"
        reason = "no_current_priority_signal"

    return InterventionItem(
        identifier=assessment.cell_id,
        priority=priority,
        reason=reason,
        abnormality_score=abnormality,
        trend_abnormality_delta=delta,
        uncertainty=uncertainty,
        evidence_count=len(assessment.evidence),
    )


def build_intervention_map(
    assessments: Dict[str, CellAssessment],
    trends: Optional[Dict[str, AssessmentTrend]] = None,
) -> Dict[str, InterventionItem]:
    """Build transparent observation priorities for assessed cells."""
    trends = trends or {}
    return {
        cell_id: classify_priority(assessment, trends.get(cell_id))
        for cell_id, assessment in assessments.items()
    }
