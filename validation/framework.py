"""Reproducible validation primitives for research models.

This module evaluates predictions against reference labels without making
clinical claims or selecting a treatment.
"""

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Optional


@dataclass(frozen=True)
class ValidationCase:
    case_id: str
    prediction: float
    reference: float
    quality_score: float = 1.0
    subgroup: Optional[str] = None


@dataclass(frozen=True)
class ValidationResult:
    n: int
    mean_absolute_error: Optional[float]
    root_mean_squared_error: Optional[float]
    mean_bias: Optional[float]
    insufficient_evidence: bool


class ValidationFramework:
    """Calculate transparent aggregate errors for a validation dataset."""

    def __init__(self, minimum_quality: float = 0.5, minimum_cases: int = 2) -> None:
        if not 0 <= minimum_quality <= 1:
            raise ValueError("minimum_quality must be between 0 and 1")
        if minimum_cases < 1:
            raise ValueError("minimum_cases must be positive")
        self.minimum_quality = minimum_quality
        self.minimum_cases = minimum_cases

    def evaluate(self, cases: Iterable[ValidationCase]) -> ValidationResult:
        valid = [
            case for case in cases
            if case.quality_score >= self.minimum_quality
            and all(isfinite(v) for v in (case.prediction, case.reference, case.quality_score))
        ]
        if len(valid) < self.minimum_cases:
            return ValidationResult(0, None, None, None, True)

        errors = [case.prediction - case.reference for case in valid]
        mae = sum(abs(error) for error in errors) / len(errors)
        rmse = (sum(error * error for error in errors) / len(errors)) ** 0.5
        bias = sum(errors) / len(errors)
        return ValidationResult(len(valid), mae, rmse, bias, False)

    def evaluate_subgroups(self, cases: Iterable[ValidationCase]) -> dict[str, ValidationResult]:
        groups: dict[str, list[ValidationCase]] = {}
        for case in cases:
            key = case.subgroup or "all"
            groups.setdefault(key, []).append(case)
        return {key: self.evaluate(group) for key, group in groups.items()}
