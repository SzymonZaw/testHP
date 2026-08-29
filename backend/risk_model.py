"""Explainable aggregation of non-diagnostic longitudinal risk signals."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .risk_signal import RiskSignal


_LEVELS = {"low": 0, "moderate": 1, "elevated": 2, "high": 3}


@dataclass(frozen=True)
class RiskModel:
    """Aggregates observed signals without making a diagnosis or treatment decision."""

    overall_level: str
    confidence: float
    signals: tuple[RiskSignal, ...]
    regions: tuple[str, ...]

    @classmethod
    def from_signals(cls, signals: Iterable[RiskSignal]) -> "RiskModel":
        items = tuple(signals)
        if not items:
            return cls("insufficient_data", 0.0, (), ())

        max_level = max((_LEVELS.get(signal.severity, 0) for signal in items), default=0)
        overall_level = next(level for level, value in _LEVELS.items() if value == max_level)
        confidence = sum(max(0.0, min(1.0, signal.confidence)) for signal in items) / len(items)
        regions = tuple(sorted({signal.region for signal in items if signal.region is not None}))
        return cls(overall_level, confidence, items, regions)

    @property
    def signal_types(self) -> tuple[str, ...]:
        return tuple(sorted({signal.signal_type for signal in self.signals}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_level": self.overall_level,
            "confidence": self.confidence,
            "signal_types": self.signal_types,
            "regions": self.regions,
            "signals": [signal.to_dict() for signal in self.signals],
        }
