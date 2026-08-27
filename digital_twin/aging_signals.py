"""Evidence-based signals derived from longitudinal digital-twin changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

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


def build_aging_signals(trajectories: Iterable[RegionalTrajectory]) -> List[AgingSignal]:
    """Build signals for a collection of regional/tissue trajectories."""
    signals: List[AgingSignal] = []
    for trajectory in trajectories:
        signals.extend(signals_from_trajectory(trajectory))
    return signals
