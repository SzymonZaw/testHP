"""Evidence-based signals derived from longitudinal digital-twin changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from .evidence import Evidence, evidence_summary
from .regional_trajectory import RegionalTrajectory


@dataclass(frozen=True)
class AgingSignal:
    """An observational signal, not a diagnosis or treatment recommendation."""

    structure_id: str
    structure_type: str
    signal_type: str
    severity: str
    direction: str
    magnitude: Optional[float]
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    evidence_records: List[Evidence] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))
        object.__setattr__(self, "evidence_records", list(self.evidence_records))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "structure_id": self.structure_id,
            "structure_type": self.structure_type,
            "signal_type": self.signal_type,
            "severity": self.severity,
            "direction": self.direction,
            "magnitude": self.magnitude,
            "confidence": self.confidence,
            "evidence": dict(self.evidence),
            "evidence_records": [item.to_dict() for item in self.evidence_records],
        }


def _severity(magnitude: Optional[float], confidence: float) -> str:
    if magnitude is None or confidence < 0.5:
        return "insufficient"
    value = abs(magnitude)
    if value >= 10:
        return "high"
    if value >= 5:
        return "moderate"
    return "low"


def signals_from_trajectory(trajectory: RegionalTrajectory) -> List[AgingSignal]:
    """Convert a trajectory into conservative, explainable observational signals."""
    signals: List[AgingSignal] = []
    confidence = max(0.0, min(1.0, trajectory.confidence))

    if trajectory.age_change is not None and trajectory.age_change > 0.5:
        signals.append(AgingSignal(
            trajectory.structure_id,
            trajectory.structure_type,
            "accelerated_aging",
            _severity(trajectory.age_change, confidence),
            "increasing",
            trajectory.age_change,
            confidence,
            {"age_slope_per_day": trajectory.age_slope_per_day},
        ))

    abnormal_delta = trajectory.health_change.get("abnormal", 0)
    if abnormal_delta > 0:
        signals.append(AgingSignal(
            trajectory.structure_id,
            trajectory.structure_type,
            "abnormal_population_increase",
            _severity(float(abnormal_delta), confidence),
            "increasing",
            float(abnormal_delta),
            confidence,
            {"health_change": trajectory.health_change},
        ))

    impaired_delta = trajectory.function_change.get("impaired", 0)
    if impaired_delta > 0:
        signals.append(AgingSignal(
            trajectory.structure_id,
            trajectory.structure_type,
            "functional_decline",
            _severity(float(impaired_delta), confidence),
            "decreasing",
            float(impaired_delta),
            confidence,
            {"function_change": trajectory.function_change},
        ))

    return signals


def attach_evidence(
    signal: AgingSignal,
    evidence_records: Iterable[Evidence],
) -> AgingSignal:
    """Attach traceable evidence and recompute effective signal confidence."""
    records = list(evidence_records)
    summary = evidence_summary(records)
    effective = min(signal.confidence, float(summary["confidence"])) if records else signal.confidence
    merged_evidence = {**signal.evidence, "evidence_summary": summary}
    return AgingSignal(
        structure_id=signal.structure_id,
        structure_type=signal.structure_type,
        signal_type=signal.signal_type,
        severity=_severity(signal.magnitude, effective),
        direction=signal.direction,
        magnitude=signal.magnitude,
        confidence=effective,
        evidence=merged_evidence,
        evidence_records=records,
    )


def evidence_from_trajectory(
    trajectory: RegionalTrajectory,
    *,
    source_type: str = "longitudinal_observation",
) -> List[Evidence]:
    """Create one traceable evidence record per trajectory point."""
    records: List[Evidence] = []
    for point in trajectory.points:
        observed_at = datetime.fromisoformat(point["observed_at"])
        records.append(Evidence(
            evidence_id=f"{trajectory.structure_id}:{point['observation_id']}",
            source_type=source_type,
            source_id=point["observation_id"],
            observed_at=observed_at,
            feature=f"{trajectory.structure_type}.{trajectory.structure_id}",
            value={
                "biological_age": point.get("biological_age"),
                "health_distribution": point.get("health_distribution", {}),
                "function_distribution": point.get("function_distribution", {}),
            },
            confidence=float(point.get("confidence", 0.0)),
        ))
    return records


def build_aging_signals(trajectories: Iterable[RegionalTrajectory]) -> List[AgingSignal]:
    """Build signals with traceable trajectory evidence attached."""
    signals: List[AgingSignal] = []
    for trajectory in trajectories:
        for signal in signals_from_trajectory(trajectory):
            signals.append(attach_evidence(signal, evidence_from_trajectory(trajectory)))
    return signals
