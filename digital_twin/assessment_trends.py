"""Longitudinal change detection for hierarchical assessments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .cell_assessment import CellAssessment
from .hierarchical_assessment import LevelAssessment


@dataclass
class AssessmentTrend:
    """Change between two assessment snapshots, without clinical action."""

    level: str
    identifier: str
    from_observed_at: str
    to_observed_at: str
    health_score_delta: Optional[float]
    abnormality_delta: Optional[float]
    biological_age_delta: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def compare_cell_assessments(previous: CellAssessment, current: CellAssessment) -> AssessmentTrend:
    return AssessmentTrend(
        level="cell",
        identifier=current.cell_id,
        from_observed_at=previous.observed_at.isoformat(),
        to_observed_at=current.observed_at.isoformat(),
        health_score_delta=_delta(previous.health_score, current.health_score),
        abnormality_delta=_delta(previous.abnormality_score, current.abnormality_score),
        biological_age_delta=_delta(previous.biological_age, current.biological_age),
    )


def compare_level_assessments(previous: LevelAssessment, current: LevelAssessment) -> AssessmentTrend:
    return AssessmentTrend(
        level=current.level,
        identifier=current.identifier,
        from_observed_at="snapshot",
        to_observed_at="snapshot",
        health_score_delta=_delta(previous.health_score_mean, current.health_score_mean),
        abnormality_delta=_delta(previous.abnormality_mean, current.abnormality_mean),
        biological_age_delta=_delta(previous.biological_age_mean, current.biological_age_mean),
    )


def _delta(previous: Optional[float], current: Optional[float]) -> Optional[float]:
    if previous is None or current is None:
        return None
    return float(current - previous)
