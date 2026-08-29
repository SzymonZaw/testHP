"""Evaluation metrics for cell health and biological-age models."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Sequence

from .ml_contracts import CellModel, ModelInput


@dataclass(frozen=True)
class ClassificationMetrics:
    accuracy: float
    precision: float
    recall: float
    specificity: float
    balanced_accuracy: float
    brier_score: float


@dataclass(frozen=True)
class RegressionMetrics:
    mae: float
    rmse: float
    bias: float


def evaluate_classifier(model: CellModel, inputs: Sequence[ModelInput], labels: Sequence[int], positive_label: str = "pathological") -> ClassificationMetrics:
    if not inputs or len(inputs) != len(labels):
        raise ValueError("inputs and labels must be non-empty and have equal length")
    tp = tn = fp = fn = 0
    brier = 0.0
    for item, target in zip(inputs, labels):
        output = model.predict(item)
        predicted = 1 if output.prediction == positive_label else 0
        probability = float(output.probabilities.get(positive_label, predicted))
        tp += predicted == 1 and target == 1
        tn += predicted == 0 and target == 0
        fp += predicted == 1 and target == 0
        fn += predicted == 0 and target == 1
        brier += (probability - target) ** 2
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return ClassificationMetrics(accuracy, precision, recall, specificity, (recall + specificity) / 2.0, brier / total)


def evaluate_regressor(predictions: Sequence[float], targets: Sequence[float]) -> RegressionMetrics:
    if not predictions or len(predictions) != len(targets):
        raise ValueError("predictions and targets must be non-empty and have equal length")
    errors = [float(p) - float(t) for p, t in zip(predictions, targets)]
    return RegressionMetrics(sum(abs(e) for e in errors) / len(errors), sqrt(sum(e * e for e in errors) / len(errors)), sum(errors) / len(errors))
