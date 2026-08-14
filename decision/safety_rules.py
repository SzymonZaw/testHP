from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyResult:
    """Result of the research decision safety gate."""

    allowed: bool
    risk_level: str
    warnings: list[str]
    reasons: list[str]


class SafetyRules:
    """Conservative safety gate for research-level decision support."""

    def __init__(
        self,
        minimum_confidence: float = 0.50,
        high_risk_threshold: float = 0.85,
        moderate_risk_threshold: float = 0.65,
        high_abnormality_threshold: float = 0.85,
    ) -> None:
        self.minimum_confidence = float(minimum_confidence)
        self.high_risk_threshold = float(high_risk_threshold)
        self.moderate_risk_threshold = float(moderate_risk_threshold)
        self.high_abnormality_threshold = float(high_abnormality_threshold)

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def evaluate(
        self,
        confidence: float,
        risk_score: float = 0.0,
        data_complete: bool = True,
        multimodal_consistent: bool = True,
        temporal_data_available: bool = True,
        abnormality_score: float = 0.0,
    ) -> SafetyResult:
        confidence = self._clip(confidence)
        risk_score = self._clip(risk_score)
        abnormality_score = self._clip(abnormality_score)

        warnings: list[str] = []
        reasons: list[str] = []
        allowed = True

        if confidence < self.minimum_confidence:
            allowed = False
            warnings.append("insufficient_confidence")
            reasons.append("Confidence is below the safety threshold.")

        if not data_complete:
            allowed = False
            warnings.append("incomplete_data")
            reasons.append("Required data are incomplete.")

        if not multimodal_consistent:
            allowed = False
            warnings.append("multimodal_inconsistency")
            reasons.append("Available modalities are inconsistent.")

        if not temporal_data_available:
            warnings.append("no_longitudinal_data")
            reasons.append("No longitudinal evidence is available.")

        combined_signal = max(risk_score, abnormality_score)
        if combined_signal >= self.high_risk_threshold:
            risk_level = "high"
        elif combined_signal >= self.moderate_risk_threshold:
            risk_level = "moderate"
        elif combined_signal > 0.0:
            risk_level = "low"
        else:
            risk_level = "unknown"

        if abnormality_score >= self.high_abnormality_threshold:
            warnings.append("high_abnormality_signal")
            reasons.append("A high abnormality signal requires additional review.")

        if not reasons:
            reasons.append("No safety rule was triggered by the supplied evidence.")

        return SafetyResult(
            allowed=allowed,
            risk_level=risk_level,
            warnings=warnings,
            reasons=reasons,
        )


__all__ = ["SafetyRules", "SafetyResult"]
