"""Longitudinal surveillance primitives for research interventions.

This module records observations; it does not recommend, prescribe, or approve
an intervention. Efficacy and safety are intentionally tracked separately.
"""

from dataclasses import dataclass, field
from typing import Iterable, Optional


@dataclass(frozen=True)
class InterventionObservation:
    timepoint_id: str
    timestamp: float
    domain: str
    value: float
    quality_score: float = 1.0
    direction: str = "neutral"
    source: Optional[str] = None


@dataclass(frozen=True)
class SurveillanceSummary:
    intervention_id: str
    efficacy_change: Optional[float]
    safety_change: Optional[float]
    efficacy_points: int
    safety_points: int
    insufficient_evidence: bool
    safety_signal: bool


@dataclass
class InterventionSurveillance:
    """Stores separate longitudinal efficacy and safety observations."""

    intervention_id: str
    observations: list[InterventionObservation] = field(default_factory=list)

    def add(self, observation: InterventionObservation) -> None:
        if not 0 <= observation.quality_score <= 1:
            raise ValueError("quality_score must be between 0 and 1")
        if observation.domain not in {"efficacy", "safety"}:
            raise ValueError("domain must be 'efficacy' or 'safety'")
        self.observations.append(observation)
        self.observations.sort(key=lambda item: item.timestamp)

    def observations_for(self, domain: str, minimum_quality: float = 0.5) -> tuple[InterventionObservation, ...]:
        return tuple(
            item for item in self.observations
            if item.domain == domain and item.quality_score >= minimum_quality
        )

    def _change(self, values: Iterable[InterventionObservation]) -> Optional[float]:
        points = tuple(values)
        if len(points) < 2:
            return None
        return points[-1].value - points[0].value

    def summary(self, minimum_quality: float = 0.5, safety_threshold: float = 0.0) -> SurveillanceSummary:
        efficacy = self.observations_for("efficacy", minimum_quality)
        safety = self.observations_for("safety", minimum_quality)
        efficacy_change = self._change(efficacy)
        safety_change = self._change(safety)
        insufficient = len(efficacy) < 2 or len(safety) < 2
        safety_signal = safety_change is not None and safety_change > safety_threshold
        return SurveillanceSummary(
            intervention_id=self.intervention_id,
            efficacy_change=efficacy_change,
            safety_change=safety_change,
            efficacy_points=len(efficacy),
            safety_points=len(safety),
            insufficient_evidence=insufficient,
            safety_signal=safety_signal,
        )
