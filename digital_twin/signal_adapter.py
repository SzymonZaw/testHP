"""Adapters between digital-twin observational signals and anomaly screening."""
from __future__ import annotations

from typing import Iterable, List

from anomaly.detector import Anomaly
from .aging_signals import AgingSignal


def signal_to_anomalies(signal: AgingSignal) -> List[Anomaly]:
    """Convert one observational signal into the existing anomaly contract."""
    if signal.magnitude is None:
        return []
    feature = f"{signal.structure_type}.{signal.structure_id}.{signal.signal_type}"
    threshold = abs(float(signal.magnitude))
    severity = signal.severity
    if severity == "insufficient":
        return []
    reason = f"digital-twin signal ({signal.direction}, confidence={signal.confidence:.3f})"
    return [Anomaly(
        feature=feature,
        value=float(signal.magnitude),
        z_score=None,
        threshold=threshold if threshold > 0 else 1.0,
        severity=severity,
        reason=reason,
    )]


def signals_to_anomalies(signals: Iterable[AgingSignal]) -> List[Anomaly]:
    """Convert multiple digital-twin signals without changing their evidence."""
    anomalies: List[Anomaly] = []
    for signal in signals:
        anomalies.extend(signal_to_anomalies(signal))
    return anomalies
