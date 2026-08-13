"""Separate ageing-associated trajectories from pathology signals.

This is an evidence-classification primitive, not a diagnostic model.
"""

from dataclasses import dataclass
from typing import Literal


Category = Literal["normal_variation", "age_associated", "pathology_signal", "intervention_response", "insufficient_evidence"]


@dataclass(frozen=True)
class TrajectoryEvidence:
    feature: str
    trend: float
    age_association: float
    pathology_evidence: float
    intervention_context: bool = False
    sufficient_evidence: bool = True


class AgeingPathologyClassifier:
    def classify(self, evidence: TrajectoryEvidence) -> Category:
        if not evidence.sufficient_evidence:
            return "insufficient_evidence"
        if evidence.intervention_context:
            return "intervention_response"
        if evidence.pathology_evidence > evidence.age_association and evidence.pathology_evidence > 0:
            return "pathology_signal"
        if evidence.age_association > 0:
            return "age_associated"
        return "normal_variation"
