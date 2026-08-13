# decision/monitoring_rules.py

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Sequence, Optional


@dataclass
class MonitoringResult:
    """
    Wynik analizy trendu.
    """

    trend: str
    change: float
    relative_change: float
    alert: bool
    explanation: str


class MonitoringRules:
    """
    Analizuje zmiany wartości w kolejnych punktach czasowych.
    """

    def __init__(
        self,
        change_threshold: float = 0.10,
        alert_threshold: float = 0.20,
    ):
        self.change_threshold = change_threshold
        self.alert_threshold = alert_threshold

    def analyze_trend(
        self,
        values: Sequence[float],
    ) -> MonitoringResult:

        if len(values) < 2:
            return MonitoringResult(
                trend="insufficient_data",
                change=0.0,
                relative_change=0.0,
                alert=False,
                explanation=(
                    "At least two temporal measurements "
                    "are required."
                ),
            )

        start = float(values[0])
        end = float(values[-1])

        change = end - start

        if abs(start) > 1e-8:
            relative_change = change / abs(start)
        else:
            relative_change = 0.0

        if relative_change > self.change_threshold:
            trend = "increasing"
        elif relative_change < -self.change_threshold:
            trend = "decreasing"
        else:
            trend = "stable"

        alert = abs(relative_change) >= self.alert_threshold

        explanation = (
            f"Trend={trend}; "
            f"absolute change={change:.4f}; "
            f"relative change={relative_change:.2%}."
        )

        return MonitoringResult(
            trend=trend,
            change=float(change),
            relative_change=float(relative_change),
            alert=alert,
            explanation=explanation,
        )

    def compare_timepoints(
        self,
        timepoints: Dict[str, float],
    ) -> MonitoringResult:

        if len(timepoints) < 2:
            return MonitoringResult(
                trend="insufficient_data",
                change=0.0,
                relative_change=0.0,
                alert=False,
                explanation="Insufficient timepoints.",
            )

        ordered_keys = list(timepoints.keys())

        values = [
            timepoints[key]
            for key in ordered_keys
        ]

        return self.analyze_trend(values)

    def detect_progression(
        self,
        values: Sequence[float],
        worsening_direction: str = "increase",
    ) -> bool:
        """
        Sprawdza, czy trend wskazuje potencjalne pogorszenie.

        worsening_direction:
            "increase" -> większa wartość = gorzej
            "decrease" -> mniejsza wartość = gorzej
        """

        result = self.analyze_trend(values)

        if worsening_direction == "increase":
            return (
                result.trend == "increasing"
                and result.alert
            )

        if worsening_direction == "decrease":
            return (
                result.trend == "decreasing"
                and result.alert
            )

        raise ValueError(
            "worsening_direction must be "
            "'increase' or 'decrease'."
        )


if __name__ == "__main__":
    monitoring = MonitoringRules()

    result = monitoring.analyze_trend(
        [0.31, 0.34, 0.39, 0.46]
    )

    print(result)

    progression = monitoring.detect_progression(
        [0.31, 0.34, 0.39, 0.46],
        worsening_direction="increase",
    )

    print("Potential progression:", progression)