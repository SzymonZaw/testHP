"""Scientific validation and uncertainty contracts for the research twin.

The module makes scientific progress measurable instead of equating an API
existing with a biological capability being validated.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from math import sqrt
from typing import Iterable, Mapping, Sequence


class EvidenceLevel(IntEnum):
    SYNTHETIC = 0
    IMAGE_DERIVED = 1
    LABELED_BENCHMARK = 2
    INTERNAL_VALIDATION = 3
    EXTERNAL_VALIDATION = 4
    LONGITUDINAL = 5
    PROSPECTIVE = 6
    CLINICAL = 7


@dataclass(frozen=True)
class Evidence:
    level: EvidenceLevel
    sources: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()

    @property
    def validated(self) -> bool:
        return self.level >= EvidenceLevel.EXTERNAL_VALIDATION


@dataclass(frozen=True)
class PredictionRecord:
    subject_id: str
    observed_at: float
    horizon_years: float
    prediction: float
    uncertainty: float
    model_version: str
    evidence: Evidence


@dataclass(frozen=True)
class CalibrationReport:
    count: int
    mae: float
    rmse: float
    mean_interval_width: float
    coverage: float
    model_version: str
    passed: bool


class PredictionValidator:
    """Evaluate forecasts against later observations without hiding error."""

    def evaluate(
        self,
        records: Sequence[PredictionRecord],
        observed_values: Mapping[str, float],
        *,
        interval_z: float = 1.96,
        max_mae: float | None = None,
        min_coverage: float | None = None,
    ) -> CalibrationReport:
        if not records:
            raise ValueError("at least one prediction record is required")
        if interval_z <= 0:
            raise ValueError("interval_z must be positive")
        errors: list[float] = []
        widths: list[float] = []
        covered = 0
        for record in records:
            if record.subject_id not in observed_values:
                continue
            actual = float(observed_values[record.subject_id])
            error = record.prediction - actual
            errors.append(error)
            width = interval_z * max(0.0, float(record.uncertainty))
            widths.append(2.0 * width)
            if abs(error) <= width:
                covered += 1
        if not errors:
            raise ValueError("no prediction records have matching observations")
        mae = sum(abs(e) for e in errors) / len(errors)
        rmse = sqrt(sum(e * e for e in errors) / len(errors))
        coverage = covered / len(errors)
        passed = True
        if max_mae is not None:
            passed &= mae <= max_mae
        if min_coverage is not None:
            passed &= coverage >= min_coverage
        return CalibrationReport(
            count=len(errors),
            mae=mae,
            rmse=rmse,
            mean_interval_width=sum(widths) / len(widths),
            coverage=coverage,
            model_version=records[0].model_version,
            passed=passed,
        )


def require_evidence(evidence: Evidence, minimum: EvidenceLevel, capability: str) -> None:
    """Raise until a capability has enough evidence to be exposed as validated."""
    if evidence.level < minimum:
        raise PermissionError(
            f"{capability} requires evidence level {minimum.name}; "
            f"received {evidence.level.name}"
        )


def compare_against_baseline(errors: Iterable[float], baseline_errors: Iterable[float]) -> dict[str, float]:
    """Return a transparent paired error comparison for research benchmarks."""
    model = [abs(float(x)) for x in errors]
    baseline = [abs(float(x)) for x in baseline_errors]
    if not model or len(model) != len(baseline):
        raise ValueError("model and baseline errors must have equal non-zero length")
    model_mae = sum(model) / len(model)
    baseline_mae = sum(baseline) / len(baseline)
    improvement = 1.0 - (model_mae / baseline_mae) if baseline_mae else 0.0
    return {
        "model_mae": model_mae,
        "baseline_mae": baseline_mae,
        "relative_improvement": improvement,
    }
