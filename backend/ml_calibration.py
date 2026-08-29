"""Calibration helpers for model probabilities and predictive uncertainty."""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import pstdev
from typing import Sequence

from .ml_contracts import ModelOutput


@dataclass(frozen=True)
class CalibrationResult:
    temperature: float
    calibrated_probabilities: tuple[float, ...]
    brier_score: float


def _logit(p: float) -> float:
    p = min(1.0 - 1e-7, max(1e-7, p))
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(max(-60.0, min(60.0, -x))))


def fit_temperature(probabilities: Sequence[float], labels: Sequence[int], *, min_temperature: float = 0.25, max_temperature: float = 5.0, steps: int = 191) -> CalibrationResult:
    if not probabilities or len(probabilities) != len(labels):
        raise ValueError("probabilities and labels must be non-empty and have equal length")
    if any(label not in (0, 1) for label in labels):
        raise ValueError("labels must be binary")
    best_t = 1.0
    best_loss = float("inf")
    for index in range(steps):
        t = min_temperature + (max_temperature - min_temperature) * index / max(1, steps - 1)
        loss = 0.0
        for probability, label in zip(probabilities, labels):
            calibrated = _sigmoid(_logit(float(probability)) / t)
            loss -= label * math.log(max(calibrated, 1e-12)) + (1 - label) * math.log(max(1 - calibrated, 1e-12))
        if loss < best_loss:
            best_loss, best_t = loss, t
    calibrated = tuple(_sigmoid(_logit(float(p)) / best_t) for p in probabilities)
    brier = sum((p - y) ** 2 for p, y in zip(calibrated, labels)) / len(labels)
    return CalibrationResult(best_t, calibrated, brier)


def classification_uncertainty(outputs: Sequence[ModelOutput]) -> float:
    """Return dispersion of confidence values as a simple ensemble uncertainty."""
    if not outputs:
        raise ValueError("outputs must be non-empty")
    confidences = [float(output.confidence or 0.0) for output in outputs]
    return pstdev(confidences) if len(confidences) > 1 else 1.0 - confidences[0]
