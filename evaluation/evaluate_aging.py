"""
Evaluation utilities for the skin biological-aging model.

Supported tasks:
- regression metrics,
- age prediction error analysis,
- subgroup evaluation,
- saving evaluation reports.

Expected predictions:
    y_pred = predicted biological age

Expected targets:
    y_true = reference chronological/biological age
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


class AgingEvaluator:
    """
    Evaluator for regression-based biological age prediction.
    """

    def __init__(self, output_dir: str = "outputs/reports/aging"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_arrays(
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        y_true = np.asarray(y_true, dtype=float).reshape(-1)
        y_pred = np.asarray(y_pred, dtype=float).reshape(-1)

        if len(y_true) != len(y_pred):
            raise ValueError(
                f"Different number of samples: "
                f"{len(y_true)} targets vs {len(y_pred)} predictions."
            )

        if len(y_true) == 0:
            raise ValueError("Evaluation arrays are empty.")

        mask = np.isfinite(y_true) & np.isfinite(y_pred)

        if not np.any(mask):
            raise ValueError("No finite samples available for evaluation.")

        return y_true[mask], y_pred[mask]

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Calculate regression metrics.

        Returns:
            MAE
            RMSE
            R2
            mean error
            median absolute error
            maximum absolute error
            bias
        """

        y_true, y_pred = self._validate_arrays(y_true, y_pred)

        errors = y_pred - y_true
        absolute_errors = np.abs(errors)

        mae = float(np.mean(absolute_errors))
        rmse = float(np.sqrt(np.mean(errors ** 2)))

        ss_res = float(np.sum(errors ** 2))
        ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))

        if ss_tot > 0:
            r2 = float(1.0 - ss_res / ss_tot)
        else:
            r2 = None

        if len(y_true) >= 2:
            correlation = float(np.corrcoef(y_true, y_pred)[0, 1])
        else:
            correlation = None

        result = {
            "task": "biological_age_regression",
            "n_samples": int(len(y_true)),
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "pearson_correlation": correlation,
            "mean_error": float(np.mean(errors)),
            "median_absolute_error": float(np.median(absolute_errors)),
            "max_absolute_error": float(np.max(absolute_errors)),
            "bias": float(np.mean(errors)),
            "target_mean": float(np.mean(y_true)),
            "prediction_mean": float(np.mean(y_pred)),
        }

        return result

    def evaluate_age_groups(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        bins: Optional[list[float]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate performance separately for age groups.

        Default:
            0-30
            30-45
            45-60
            60-75
            75+
        """

        y_true, y_pred = self._validate_arrays(y_true, y_pred)

        if bins is None:
            bins = [0, 30, 45, 60, 75, np.inf]

        result: Dict[str, Dict[str, Any]] = {}

        for lower, upper in zip(bins[:-1], bins[1:]):
            if np.isinf(upper):
                mask = y_true >= lower
                name = f"{lower}+"
            else:
                mask = (y_true >= lower) & (y_true < upper)
                name = f"{lower}-{upper}"

            if not np.any(mask):
                continue

            group_metrics = self.evaluate(
                y_true[mask],
                y_pred[mask],
            )

            result[name] = group_metrics

        return result

    def save_report(
        self,
        report: Dict[str, Any],
        filename: str = "aging_evaluation.json",
    ) -> Path:

        path = self.output_dir / filename

        with path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return path


def main() -> None:
    """
    Small smoke test.
    """

    y_true = np.array([25, 32, 41, 50, 62, 71])
    y_pred = np.array([27, 31, 43, 48, 60, 75])

    evaluator = AgingEvaluator()

    metrics = evaluator.evaluate(y_true, y_pred)
    groups = evaluator.evaluate_age_groups(y_true, y_pred)

    report = {
        "overall": metrics,
        "age_groups": groups,
    }

    path = evaluator.save_report(report)

    print("Aging evaluation:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    print(f"\nReport saved to: {path}")


if __name__ == "__main__":
    main()