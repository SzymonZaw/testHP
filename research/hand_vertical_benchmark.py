"""The first falsifiable vertical benchmark for the hand twin.

Goal: test whether adding multiscale evidence improves prediction of a future
hand-function measurement over a simple baseline. This module contains the
benchmark contract and split rules; it does not invent clinical labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .validation import Evidence, EvidenceLevel, compare_against_baseline


@dataclass(frozen=True)
class HandObservation:
    subject_id: str
    time: float
    function_value: float
    evidence: Evidence


@dataclass(frozen=True)
class BenchmarkResult:
    metric: str
    model_mae: float
    baseline_mae: float
    relative_improvement: float
    n: int
    passed: bool
    limitations: tuple[str, ...]


class HandVerticalBenchmark:
    """Prevents the project from claiming predictive progress without a baseline."""

    REQUIRED_HORIZON_YEARS = 0.25

    def evaluate(
        self,
        predictions: Mapping[str, float],
        baseline_predictions: Mapping[str, float],
        future_observations: Mapping[str, float],
        *,
        minimum_improvement: float = 0.0,
    ) -> BenchmarkResult:
        ids = set(predictions) & set(baseline_predictions) & set(future_observations)
        if not ids:
            raise ValueError("no overlapping subjects for benchmark")
        model_errors = [predictions[i] - future_observations[i] for i in sorted(ids)]
        baseline_errors = [baseline_predictions[i] - future_observations[i] for i in sorted(ids)]
        metrics = compare_against_baseline(model_errors, baseline_errors)
        return BenchmarkResult(
            metric="MAE",
            model_mae=metrics["model_mae"],
            baseline_mae=metrics["baseline_mae"],
            relative_improvement=metrics["relative_improvement"],
            n=len(ids),
            passed=metrics["relative_improvement"] >= minimum_improvement,
            limitations=(
                "Research benchmark only; not clinical validation.",
                "Performance must be confirmed on an external dataset before claims of generalization.",
                "A better predictive score does not establish causality or treatment benefit.",
            ),
        )

    @staticmethod
    def minimum_evidence() -> Evidence:
        return Evidence(
            level=EvidenceLevel.LABELED_BENCHMARK,
            sources=("future_hand_function_measurement",),
            missing=("external_validation", "prospective_validation"),
        )
