# decision/decision_engine.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Sequence

from .confidence import ConfidenceEstimator, ConfidenceResult
from .safety_rules import SafetyRules, SafetyResult
from .intervention_rules import (
    InterventionRules,
    InterventionDecision,
)
from .monitoring_rules import (
    MonitoringRules,
    MonitoringResult,
)


@dataclass
class FinalDecision:
    """
    Końcowy wynik warstwy decyzyjnej.
    """

    decision: str
    confidence: float
    confidence_level: str
    risk_level: str
    intervention_category: str
    intervention_priority: str
    monitoring_trend: str
    safety_allowed: bool
    warnings: list
    reasons: list


class DecisionEngine:
    """
    Centralny silnik decyzji.

    Łączy wyniki:
        - modeli ML,
        - analizy multimodalnej,
        - analizy ryzyka,
        - analizy longitudinalnej,
        - reguł bezpieczeństwa.
    """

    def __init__(
        self,
        confidence_estimator: Optional[
            ConfidenceEstimator
        ] = None,
        safety_rules: Optional[SafetyRules] = None,
        intervention_rules: Optional[InterventionRules] = None,
        monitoring_rules: Optional[MonitoringRules] = None,
    ):

        self.confidence_estimator = (
            confidence_estimator
            or ConfidenceEstimator()
        )

        self.safety_rules = (
            safety_rules
            or SafetyRules()
        )

        self.intervention_rules = (
            intervention_rules
            or InterventionRules()
        )

        self.monitoring_rules = (
            monitoring_rules
            or MonitoringRules()
        )

    def evaluate(
        self,
        model_confidence: float,
        data_quality: float = 1.0,
        temporal_consistency: float = 1.0,
        multimodal_consistency: float = 1.0,
        data_completeness: float = 1.0,
        risk_score: float = 0.0,
        abnormality_score: float = 0.0,
        pathology_score: float = 0.0,
        temporal_values: Optional[
            Sequence[float]
        ] = None,
        worsening_direction: str = "increase",
        data_complete: bool = True,
        multimodal_consistent: bool = True,
        temporal_data_available: bool = True,
    ) -> FinalDecision:

        # ---------------------------------------------------------
        # 1. CONFIDENCE
        # ---------------------------------------------------------

        confidence_result: ConfidenceResult = (
            self.confidence_estimator.calculate(
                model_confidence=model_confidence,
                data_quality=data_quality,
                temporal_consistency=temporal_consistency,
                multimodal_consistency=multimodal_consistency,
                data_completeness=data_completeness,
            )
        )

        # ---------------------------------------------------------
        # 2. SAFETY
        # ---------------------------------------------------------

        safety_result: SafetyResult = (
            self.safety_rules.evaluate(
                confidence=confidence_result.score,
                risk_score=risk_score,
                data_complete=data_complete,
                multimodal_consistent=multimodal_consistent,
                temporal_data_available=temporal_data_available,
                abnormality_score=abnormality_score,
            )
        )

        # ---------------------------------------------------------
        # 3. MONITORING
        # ---------------------------------------------------------

        if temporal_values is not None:
            monitoring_result = (
                self.monitoring_rules.analyze_trend(
                    temporal_values
                )
            )
        else:
            monitoring_result = MonitoringResult(
                trend="not_available",
                change=0.0,
                relative_change=0.0,
                alert=False,
                explanation="No longitudinal data supplied.",
            )

        # ---------------------------------------------------------
        # 4. INTERVENTION
        # ---------------------------------------------------------

        intervention_result: InterventionDecision = (
            self.intervention_rules.decide(
                risk_score=risk_score,
                abnormality_score=abnormality_score,
                pathology_score=pathology_score,
                confidence=confidence_result.score,
            )
        )

        # ---------------------------------------------------------
        # 5. FINAL DECISION
        # ---------------------------------------------------------

        if not safety_result.allowed:
            final_decision = "blocked"

        elif intervention_result.category == "urgent_review":
            final_decision = "urgent_review"

        elif intervention_result.category == "additional_review":
            final_decision = "additional_review"

        elif monitoring_result.alert:
            final_decision = "monitor"

        elif intervention_result.category == "monitoring":
            final_decision = "monitor"

        else:
            final_decision = "no_action_signal"

        return FinalDecision(
            decision=final_decision,
            confidence=confidence_result.score,
            confidence_level=confidence_result.level,
            risk_level=safety_result.risk_level,
            intervention_category=(
                intervention_result.category
            ),
            intervention_priority=(
                intervention_result.priority
            ),
            monitoring_trend=monitoring_result.trend,
            safety_allowed=safety_result.allowed,
            warnings=safety_result.warnings,
            reasons=safety_result.reasons,
        )

    def evaluate_dict(
        self,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        result = self.evaluate(**kwargs)

        return asdict(result)


if __name__ == "__main__":

    engine = DecisionEngine()

    result = engine.evaluate(
        model_confidence=0.91,
        data_quality=0.90,
        temporal_consistency=0.85,
        multimodal_consistency=0.88,
        data_completeness=0.95,

        risk_score=0.68,
        abnormality_score=0.55,
        pathology_score=0.60,

        temporal_values=[
            0.35,
            0.39,
            0.44,
            0.51,
        ],

        worsening_direction="increase",

        data_complete=True,
        multimodal_consistent=True,
        temporal_data_available=True,
    )

    print("\nFinal Decision")
    print("-----------------------------")

    for key, value in asdict(result).items():
        print(f"{key}: {value}")