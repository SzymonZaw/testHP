"""Trainable biological-age regression model for the cell twin.

This experimental baseline produces an auditable estimate with uncertainty;
it is not a clinical model or diagnosis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from statistics import pstdev
from typing import Any, Mapping, Sequence

from .cell_age import CellAgeEstimate
from .data_foundation import Uncertainty, utc_now
from .ml_contracts import ModelInput


@dataclass
class BiologicalAgeRegressor:
    model_id: str = "biological-cell-age-linear"
    model_version: str = "0.1.0"
    learning_rate: float = 0.01
    epochs: int = 800
    weights: dict[str, float] = field(default_factory=dict)
    bias: float = 0.0
    feature_names: tuple[str, ...] = ()
    residual_std: float | None = None
    trained: bool = False

    def fit(self, inputs: Sequence[ModelInput], target_ages: Sequence[float]) -> None:
        if not inputs or len(inputs) != len(target_ages):
            raise ValueError("inputs and target_ages must be non-empty and have equal length")
        names = tuple(sorted({name for item in inputs for name, value in item.features.items() if isinstance(value, (int, float)) and not isinstance(value, bool)}))
        if not names:
            raise ValueError("training requires numeric features")
        self.feature_names = names
        self.weights = {name: 0.0 for name in names}
        self.bias = sum(float(age) for age in target_ages) / len(target_ages)
        n = float(len(inputs))
        for _ in range(self.epochs):
            gradients = {name: 0.0 for name in names}
            bias_gradient = 0.0
            for item, target in zip(inputs, target_ages):
                prediction = self._predict_value(item)
                error = prediction - float(target)
                bias_gradient += error
                for name in names:
                    gradients[name] += error * float(item.features.get(name, 0.0))
            self.bias -= self.learning_rate * bias_gradient / n
            for name in names:
                self.weights[name] -= self.learning_rate * gradients[name] / n
        errors = [self._predict_value(item) - float(target) for item, target in zip(inputs, target_ages)]
        self.residual_std = sqrt(sum(error * error for error in errors) / len(errors)) if errors else None
        self.trained = True

    def _predict_value(self, model_input: ModelInput) -> float:
        return max(0.0, self.bias + sum(self.weights[name] * float(model_input.features.get(name, 0.0)) for name in self.feature_names))

    def predict_age(self, model_input: ModelInput) -> tuple[float, float | None, float | None]:
        model_input.validate()
        if not self.trained:
            raise RuntimeError("biological age model is not trained")
        age = self._predict_value(model_input)
        uncertainty = self.residual_std
        confidence = None if uncertainty is None else 1.0 / (1.0 + uncertainty)
        return age, uncertainty, confidence

    def to_cell_age_estimate(
        self,
        *,
        estimate_id: str,
        cell_id: str,
        model_input: ModelInput,
        evidence: tuple[Any, ...],
        provenance: Any,
        metadata: Mapping[str, object] | None = None,
    ) -> CellAgeEstimate:
        age, uncertainty_years, confidence = self.predict_age(model_input)
        interval = None if uncertainty_years is None else (max(0.0, age - uncertainty_years), age + uncertainty_years)
        estimate = CellAgeEstimate(
            estimate_id=estimate_id,
            cell_id=cell_id,
            biological_age_years=age,
            uncertainty=Uncertainty(
                kind="residual_rmse",
                score=None if confidence is None else 1.0 - confidence,
                interval=interval,
                details={"uncertainty_years": uncertainty_years},
            ),
            evidence=evidence,
            provenance=provenance,
            model_id=self.model_id,
            model_version=self.model_version,
            assessed_at=utc_now(),
            metadata={**dict(metadata or {}), "confidence": confidence, "feature_names": self.feature_names},
        )
        estimate.validate()
        return estimate
