"""Orchestrate observation, anomaly assessment and follow-up planning.

The engine is intentionally decision-support only: it does not diagnose,
prescribe treatment, or execute medical procedures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from anomaly.detector import Anomaly, AnomalyDetector
from anomaly.state_anomaly import detect_state_anomalies
from core.biological_state import BiologicalState
from decision.investigation_planner import InvestigationPlan, InvestigationPlanner
from decision.risk_assessment import RiskAssessment, RiskAssessor


@dataclass(frozen=True)
class MonitoringCycle:
    state: BiologicalState
    anomalies: tuple[Anomaly, ...]
    risk: RiskAssessment
    investigation: InvestigationPlan


class MonitoringEngine:
    """Run one repeatable monitoring cycle and retain all intermediate outputs."""

    def __init__(
        self,
        anomaly_detector: AnomalyDetector | None = None,
        risk_assessor: RiskAssessor | None = None,
        investigation_planner: InvestigationPlanner | None = None,
    ) -> None:
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.risk_assessor = risk_assessor or RiskAssessor()
        self.investigation_planner = investigation_planner or InvestigationPlanner()
        self.history: list[MonitoringCycle] = []

    def run_cycle(
        self,
        state: BiologicalState,
        reference: Mapping[str, tuple[float, float]],
        rates: Mapping[str, float] | None = None,
    ) -> MonitoringCycle:
        anomalies = detect_state_anomalies(
            state,
            reference,
            detector=self.anomaly_detector,
            rates=rates,
        )
        risk = self.risk_assessor.assess(anomalies)
        investigation = self.investigation_planner.plan(anomalies, risk.level)
        cycle = MonitoringCycle(
            state=state,
            anomalies=tuple(anomalies),
            risk=risk,
            investigation=investigation,
        )
        self.history.append(cycle)
        return cycle

    def latest(self) -> MonitoringCycle | None:
        return self.history[-1] if self.history else None
