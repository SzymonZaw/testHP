"""Prioritize follow-up observations without making treatment decisions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class ObservationPriority:
    target_id: str
    priority: str
    score: float
    reason: str
    recommended_action: str
    confidence: float

    def to_dict(self):
        return asdict(self)


def prioritize_observation(
    target_id: str,
    confidence: float,
    coverage: float,
    abnormality: Optional[float] = None,
    trend_delta: Optional[float] = None,
) -> ObservationPriority:
    confidence = max(0.0, min(1.0, confidence))
    coverage = max(0.0, min(1.0, coverage))
    abnormality = max(0.0, abnormality or 0.0)
    trend = abs(trend_delta or 0.0)
    score = min(1.0, (1.0 - confidence) * 0.45 + (1.0 - coverage) * 0.30 + min(abnormality, 1.0) * 0.15 + min(trend, 1.0) * 0.10)
    if coverage < 0.5 or confidence < 0.5:
        priority, action, reason = "collect_data", "collect_more_evidence", "insufficient confidence or coverage"
    elif score >= 0.55:
        priority, action, reason = "investigate", "review_evidence", "elevated uncertainty or change"
    elif score >= 0.30:
        priority, action, reason = "monitor", "repeat_observation", "moderate uncertainty or change"
    else:
        priority, action, reason = "observe", "no_immediate_follow_up", "stable evidence with adequate confidence"
    return ObservationPriority(target_id, priority, score, reason, action, confidence)
