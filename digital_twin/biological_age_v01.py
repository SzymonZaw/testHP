"""Research-only multi-component biological age estimate.

This module is a data contract/aggregation layer, not a clinical or diagnostic
model. Missing evidence is preserved instead of being converted into a guess.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class AgeEvidence:
    value: float
    confidence: float
    evidence_count: int = 1
    source: str = "synthetic"

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.evidence_count < 0:
            raise ValueError("evidence_count must be non-negative")


@dataclass(frozen=True)
class BiologicalAgeEstimate:
    morphology: Optional[AgeEvidence] = None
    cellular: Optional[AgeEvidence] = None
    functional: Optional[AgeEvidence] = None
    molecular: Optional[AgeEvidence] = None
    overall_age: Optional[float] = None
    confidence: float = 0.0
    evidence_count: int = 0
    status: str = "insufficient_evidence"


def estimate_biological_age(
    *,
    morphology: Optional[AgeEvidence] = None,
    cellular: Optional[AgeEvidence] = None,
    functional: Optional[AgeEvidence] = None,
    molecular: Optional[AgeEvidence] = None,
    minimum_components: int = 2,
) -> BiologicalAgeEstimate:
    """Aggregate available components without fabricating missing evidence.

    Components are weighted by confidence. Overall confidence is the weighted
    mean confidence, while evidence_count is the sum of contributing evidence.
    At least ``minimum_components`` valid components are required for an
    overall estimate; otherwise ``overall_age`` remains None.
    """
    components = [morphology, cellular, functional, molecular]
    available = [item for item in components if item is not None]
    evidence_count = sum(item.evidence_count for item in available)
    if not available or len(available) < minimum_components:
        return BiologicalAgeEstimate(
            morphology=morphology,
            cellular=cellular,
            functional=functional,
            molecular=molecular,
            confidence=(sum(item.confidence for item in available) / len(available)) if available else 0.0,
            evidence_count=evidence_count,
        )

    total_weight = sum(item.confidence for item in available)
    if total_weight <= 0:
        return BiologicalAgeEstimate(
            morphology=morphology, cellular=cellular, functional=functional,
            molecular=molecular, evidence_count=evidence_count,
        )

    overall_age = sum(item.value * item.confidence for item in available) / total_weight
    confidence = total_weight / len(available)
    return BiologicalAgeEstimate(
        morphology=morphology,
        cellular=cellular,
        functional=functional,
        molecular=molecular,
        overall_age=overall_age,
        confidence=confidence,
        evidence_count=evidence_count,
        status="estimated",
    )
