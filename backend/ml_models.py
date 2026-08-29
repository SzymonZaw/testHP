"""Small framework-free baseline ML models for the cell twin.

These models are real trainable baselines, not clinical models. They are
intended to prove the repository's data -> train -> inference path before
introducing a framework-backed research model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .data_foundation import Uncertainty
from .ml_contracts import ModelInput, ModelOutput, CellModel


@dataclass
class LogisticCellHealthModel(CellModel):
    """Binary logistic-regression model trained with batch gradient descent."""

    model_id: str = "cell-health-logistic"
    model_version: str = "0.1.0"
    positive_label: str = "pathological"
    negative_label: str = "healthy"
    learning_rate: float = 0.05
    epochs: int = 500
    weights: dict[str, float] = field(default_factory=dict)
    bias: float = 0.0
    feature_names: tuple[str, ...] = ()
    trained: bool = False

    @staticmethod
    def _sigmoid(value: float) -> float:
        value = max(-60.0, min(60.0, value))
        return 1.0 / (1.0 + math.exp(-value))

    def fit(self, inputs: Sequence[ModelInput], labels: Sequence[int]) -> None:
        if not inputs or len(inputs) != len(labels):
            raise ValueError("inputs and labels must be non-empty and have equal length")
        for item in inputs:
            item.validate()
        names = tuple(sorted({name for item in inputs for name, value in item.features.items() if isinstance(value, (int, float)) and not isinstance(value, bool)}))
        if not names:
            raise ValueError("training requires numeric features")
        if any(label not in (0, 1) for label in labels):
            raise ValueError("binary labels must be 0 or 1")
        self.feature_names = names
        self.weights = {name: 0.0 for name in names}
        self.bias = 0.0
        n = float(len(inputs))
        for _ in range(self.epochs):
            gradients = {name: 0.0 for name in names}
            bias_gradient = 0.0
            for item, target in zip(inputs, labels):
                score = self.bias + sum(self.weights[name] * float(item.features.get(name, 0.0)) for name in names)
                probability = self._sigmoid(score)
                error = probability - target
                bias_gradient += error
                for name in names:
                    gradients[name] += error * float(item.features.get(name, 0.0))
            self.bias -= self.learning_rate * bias_gradient / n
            for name in names:
                self.weights[name] -= self.learning_rate * gradients[name] / n
        self.trained = True

    def predict(self, model_input: ModelInput) -> ModelOutput:
        model_input.validate()
        if not self.trained:
            raise RuntimeError("cell health model is not trained")
        score = self.bias + sum(self.weights[name] * float(model_input.features.get(name, 0.0)) for name in self.feature_names)
        probability = self._sigmoid(score)
        prediction = self.positive_label if probability >= 0.5 else self.negative_label
        confidence = max(probability, 1.0 - probability)
        return ModelOutput(
            model_id=self.model_id,
            model_version=self.model_version,
            prediction=prediction,
            probabilities={self.negative_label: 1.0 - probability, self.positive_label: probability},
            confidence=confidence,
            uncertainty=Uncertainty(kind="classification_margin", score=1.0 - confidence, details={"margin": abs(probability - 0.5) * 2}),
            metadata={"feature_names": self.feature_names},
        )
