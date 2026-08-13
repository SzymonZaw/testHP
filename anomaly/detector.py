"""Transparent anomaly detection based on reference distributions and change rates."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping


@dataclass(frozen=True)
class Anomaly:
    feature: str
    value: float
    z_score: float | None
    threshold: float
    severity: str
    reason: str


@dataclass(frozen=True)
class AnomalyDetector:
    """Reference-based detector; this is a screening signal, not a diagnosis."""

    z_threshold: float = 3.0
    rate_thresholds: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        if self.z_threshold <= 0 or not isfinite(float(self.z_threshold)):
            raise ValueError("z_threshold must be finite and greater than zero")

    def detect(
        self,
        values: Mapping[str, float],
        reference: Mapping[str, tuple[float, float]],
        rates: Mapping[str, float] | None = None,
    ) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        rates = rates or {}
        rate_thresholds = self.rate_thresholds or {}

        for feature, value in values.items():
            value = float(value)
            if not isfinite(value):
                anomalies.append(Anomaly(feature, value, None, self.z_threshold, "critical", "non-finite value"))
                continue

            if feature in reference:
                mean, std = reference[feature]
                if std <= 0:
                    raise ValueError(f"Reference std for {feature} must be greater than zero")
                z = (value - mean) / std
                magnitude = abs(z)
                if magnitude >= self.z_threshold:
                    severity = "critical" if magnitude >= self.z_threshold * 1.5 else "high"
                    anomalies.append(Anomaly(feature, value, z, self.z_threshold, severity, "reference deviation"))

            if feature in rates and feature in rate_thresholds:
                rate = abs(float(rates[feature]))
                threshold = float(rate_thresholds[feature])
                if threshold <= 0:
                    raise ValueError(f"Rate threshold for {feature} must be greater than zero")
                if rate >= threshold:
                    anomalies.append(Anomaly(feature, value, None, threshold, "high", "abnormal change rate"))

        return anomalies


def detect_anomalies(
    values: Mapping[str, float],
    reference: Mapping[str, tuple[float, float]],
    z_threshold: float = 3.0,
) -> list[Anomaly]:
    """Convenience wrapper for reference-based screening."""
    return AnomalyDetector(z_threshold=z_threshold).detect(values, reference)
