"""
Evaluation utilities for risk prediction.

Expected model output:
    probability of the target event.

Label convention:
    0 = event absent
    1 = event present

Supports:
- ROC-AUC
- PR-AUC
- accuracy
- precision
- recall
- specificity
- F1
- Brier score
- calibration error
- threshold analysis
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


class RiskEvaluator:
    """
    Evaluates probabilistic risk predictions.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        output_dir: str = "outputs/reports/risk",
    ):
        self.threshold = float(threshold)

        if not 0.0 < self.threshold < 1.0:
            raise ValueError(
                "threshold must be between 0 and 1."
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _validate(
        y_true: np.ndarray,
        probabilities: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:

        y_true = np.asarray(y_true).reshape(-1)

        probabilities = np.asarray(
            probabilities,
            dtype=float,
        ).reshape(-1)

        if len(y_true) != len(probabilities):
            raise ValueError(
                "y_true and probabilities must "
                "have the same length."
            )

        if len(y_true) == 0:
            raise ValueError(
                "Evaluation arrays are empty."
            )

        if not np.all(
            np.isin(
                y_true,
                [0, 1],
            )
        ):
            raise ValueError(
                "y_true must contain only 0 and 1."
            )

        if np.any(
            (probabilities < 0)
            | (probabilities > 1)
        ):
            raise ValueError(
                "Risk probabilities must be in [0, 1]."
            )

        return (
            y_true.astype(int),
            probabilities,
        )

    @staticmethod
    def _confusion(
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, int]:

        tp = int(
            np.sum(
                (y_true == 1)
                & (y_pred == 1)
            )
        )

        tn = int(
            np.sum(
                (y_true == 0)
                & (y_pred == 0)
            )
        )

        fp = int(
            np.sum(
                (y_true == 0)
                & (y_pred == 1)
            )
        )

        fn = int(
            np.sum(
                (y_true == 1)
                & (y_pred == 0)
            )
        )

        return {
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
        }

    @staticmethod
    def brier_score(
        y_true: np.ndarray,
        probabilities: np.ndarray,
    ) -> float:

        return float(
            np.mean(
                (
                    probabilities
                    - y_true
                ) ** 2
            )
        )

    def calibration_error(
        self,
        y_true: np.ndarray,
        probabilities: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """
        Estimate expected calibration error (ECE).
        """

        y_true, probabilities = self._validate(
            y_true,
            probabilities,
        )

        bins = np.linspace(
            0.0,
            1.0,
            n_bins + 1,
        )

        ece = 0.0

        for index in range(n_bins):

            lower = bins[index]
            upper = bins[index + 1]

            if index == n_bins - 1:
                mask = (
                    (probabilities >= lower)
                    & (probabilities <= upper)
                )
            else:
                mask = (
                    (probabilities >= lower)
                    & (probabilities < upper)
                )

            if not np.any(mask):
                continue

            confidence = float(
                np.mean(
                    probabilities[mask]
                )
            )

            observed_frequency = float(
                np.mean(
                    y_true[mask]
                )
            )

            weight = float(
                np.mean(mask)
            )

            ece += weight * abs(
                confidence
                - observed_frequency
            )

        return float(ece)

    def evaluate(
        self,
        y_true: np.ndarray,
        probabilities: np.ndarray,
    ) -> Dict[str, Any]:

        y_true, probabilities = self._validate(
            y_true,
            probabilities,
        )

        y_pred = (
            probabilities >= self.threshold
        ).astype(int)

        cm = self._confusion(
            y_true,
            y_pred,
        )

        tp = cm["true_positive"]
        tn = cm["true_negative"]
        fp = cm["false_positive"]
        fn = cm["false_negative"]

        total = tp + tn + fp + fn

        accuracy = (
            (tp + tn) / total
            if total > 0
            else 0.0
        )

        precision = (
            tp / (tp + fp)
            if tp + fp > 0
            else 0.0
        )

        recall = (
            tp / (tp + fn)
            if tp + fn > 0
            else 0.0
        )

        specificity = (
            tn / (tn + fp)
            if tn + fp > 0
            else 0.0
        )

        f1 = (
            2 * precision * recall
            / (precision + recall)
            if precision + recall > 0
            else 0.0
        )

        report: Dict[str, Any] = {
            "task": "risk_prediction",
            "threshold": self.threshold,
            "n_samples": int(total),
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall_sensitivity": float(recall),
            "specificity": float(specificity),
            "f1": float(f1),
            "brier_score": self.brier_score(
                y_true,
                probabilities,
            ),
            "expected_calibration_error": (
                self.calibration_error(
                    y_true,
                    probabilities,
                )
            ),
            **cm,
        }

        try:

            from sklearn.metrics import (
                average_precision_score,
                roc_auc_score,
            )

            if len(np.unique(y_true)) == 2:

                report["roc_auc"] = float(
                    roc_auc_score(
                        y_true,
                        probabilities,
                    )
                )

                report["pr_auc"] = float(
                    average_precision_score(
                        y_true,
                        probabilities,
                    )
                )

            else:

                report["roc_auc"] = None
                report["pr_auc"] = None

        except ImportError:

            report["roc_auc"] = None
            report["pr_auc"] = None

        return report

    def threshold_analysis(
        self,
        y_true: np.ndarray,
        probabilities: np.ndarray,
        thresholds: Optional[np.ndarray] = None,
    ) -> list[Dict[str, float]]:

        y_true, probabilities = self._validate(
            y_true,
            probabilities,
        )

        if thresholds is None:
            thresholds = np.linspace(
                0.05,
                0.95,
                19,
            )

        results = []

        for threshold in thresholds:

            predictions = (
                probabilities >= threshold
            ).astype(int)

            cm = self._confusion(
                y_true,
                predictions,
            )

            tp = cm["true_positive"]
            tn = cm["true_negative"]
            fp = cm["false_positive"]
            fn = cm["false_negative"]

            precision = (
                tp / (tp + fp)
                if tp + fp > 0
                else 0.0
            )

            recall = (
                tp / (tp + fn)
                if tp + fn > 0
                else 0.0
            )

            specificity = (
                tn / (tn + fp)
                if tn + fp > 0
                else 0.0
            )

            f1 = (
                2 * precision * recall
                / (precision + recall)
                if precision + recall > 0
                else 0.0
            )

            results.append(
                {
                    "threshold": float(threshold),
                    "precision": float(precision),
                    "recall": float(recall),
                    "specificity": float(specificity),
                    "f1": float(f1),
                }
            )

        return results

    def save_report(
        self,
        report: Dict[str, Any],
        filename: str = "risk_evaluation.json",
    ) -> Path:

        path = self.output_dir / filename

        with path.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                report,
                f,
                indent=2,
                ensure_ascii=False,
            )

        return path


def main() -> None:

    y_true = np.array(
        [
            0, 0, 0, 0,
            1, 1, 1, 1,
            1, 0,
        ]
    )

    probabilities = np.array(
        [
            0.05,
            0.15,
            0.25,
            0.40,
            0.90,
            0.80,
            0.75,
            0.60,
            0.55,
            0.20,
        ]
    )

    evaluator = RiskEvaluator(
        threshold=0.5
    )

    report = evaluator.evaluate(
        y_true,
        probabilities,
    )

    report["threshold_analysis"] = (
        evaluator.threshold_analysis(
            y_true,
            probabilities,
        )
    )

    path = evaluator.save_report(report)

    print("Risk evaluation:")

    for key, value in report.items():

        if key != "threshold_analysis":
            print(f"{key}: {value}")

    print(f"\nReport saved to: {path}")


if __name__ == "__main__":
    main()