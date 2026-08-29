"""Non-diagnostic signals derived from a longitudinal hand assessment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .hand_assessment import HandAssessment


@dataclass(frozen=True)
class RiskSignal:
    """A model-observed change that merits further analysis."""

    signal_type: str
    severity: str
    confidence: float
    region: str | None
    evidence: dict[str, Any]

    @classmethod
    def from_assessment(cls, assessment: HandAssessment) -> tuple["RiskSignal", ...]:
        signals: list[RiskSignal] = []
        if assessment.health_signal == "changing":
            signals.append(cls(
                signal_type="health_change",
                severity="moderate" if assessment.evidence.get("health_change_magnitude", 0) < 0.15 else "high",
                confidence=_confidence(assessment),
                region=None,
                evidence={"health_change_magnitude": assessment.evidence.get("health_change_magnitude", 0)},
            ))
        if assessment.function_signal == "changing":
            signals.append(cls(
                signal_type="function_change",
                severity="moderate" if assessment.evidence.get("function_change_magnitude", 0) < 0.15 else "high",
                confidence=_confidence(assessment),
                region=None,
                evidence={"function_change_magnitude": assessment.evidence.get("function_change_magnitude", 0)},
            ))
        for region in assessment.affected_regions:
            signals.append(cls(
                signal_type="regional_change",
                severity="moderate",
                confidence=_confidence(assessment),
                region=region,
                evidence={"region": region},
            ))
        return tuple(signals)

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "region": self.region,
            "evidence": self.evidence,
        }


def _confidence(assessment: HandAssessment) -> float:
    """Conservative confidence derived from the assessment evidence."""
    return float(assessment.evidence.get("confidence", 0.0))
