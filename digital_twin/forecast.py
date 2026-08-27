"""Conservative forecasting based on observed inference trends."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Forecast:
    cell_id: str
    current_age: Optional[float]
    age_30d: Optional[float]
    age_90d: Optional[float]
    age_180d: Optional[float]
    trajectory: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def forecast_cell(cell_id: str, inference: Any, trend: Any) -> Forecast:
    age = getattr(inference, "biological_age", None)
    confidence = float(getattr(inference, "confidence", 0.0) or 0.0)

    if age is None:
        return Forecast(cell_id, None, None, None, None, "unknown", confidence)

    direction = getattr(trend, "direction", "stable") if trend else "stable"
    step = 0.0
    if direction == "aging":
        step = 0.02 * max(confidence, 0.25)
    elif direction == "rejuvenating":
        step = -0.01 * max(confidence, 0.25)

    return Forecast(
        cell_id=cell_id,
        current_age=float(age),
        age_30d=round(float(age) + step * 30, 3),
        age_90d=round(float(age) + step * 90, 3),
        age_180d=round(float(age) + step * 180, 3),
        trajectory=direction,
        confidence=confidence,
    )
