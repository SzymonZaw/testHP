from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ForecastHorizon(str, Enum):
    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


@dataclass(frozen=True)
class PredictiveModelRef:
    model_id: str
    model_version: str
    validation_dataset_id: str | None = None
    prospective_validation_status: str = "not_validated"


@dataclass(frozen=True)
class Forecast:
    horizon: ForecastHorizon
    target_time: str
    values: dict[str, float]
    lower_bounds: dict[str, float] | None = None
    upper_bounds: dict[str, float] | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class PredictiveTwin:
    twin_id: str
    baseline_state_id: str
    model: PredictiveModelRef
    forecasts: tuple[Forecast, ...]
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.twin_id or not self.baseline_state_id or not self.forecasts:
            raise ValueError("predictive twin requires identity, baseline and forecasts")
        for forecast in self.forecasts:
            if forecast.confidence is not None and not 0 <= forecast.confidence <= 1:
                raise ValueError("confidence must be between 0 and 1")
