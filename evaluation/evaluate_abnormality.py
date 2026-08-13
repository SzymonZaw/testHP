"""
Evaluation utilities for abnormality detection.

Expected task:
    normal vs abnormal

Supports:
- accuracy
- precision
- recall / sensitivity
- specificity
- F1
- balanced accuracy
- confusion matrix
- ROC-AUC when probabilities are available
- PR-AUC when probabilities are available
- threshold analysis
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


class AbnormalityEvaluator:
    """
    Evaluates binary abnormality detection.

    Label convention:
        0 = normal
        1 = abnormal
    """

    def __init__(
        self,
        threshold: float = 0.5,
        output_dir: str = "outputs/reports/abnormality",
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
    def _validate_labels(
        y_true: np.ndarray,
    ) -> np.ndarray:

        y_true = np.asarray(y_true).reshape(-1)

        if len(y_true) == 0:
            raise ValueError(
                "y_true is empty."
            )

        unique = np.unique(y_true)

        if not np.all(
            np.isin(unique, [0, 1])
        ):
            raise ValueError(
                "y_true must contain only 0 and 1."
            )

        return y_true.astype(int)

    @staticmethod
    def _validate_probabilities(
        probabilities: np.ndarray,
    ) -> np.ndarray:

        probabilities = np.asarray(
            probabilities,
            dtype=float,
        ).reshape(-1)

        if len(probabilities) == 0:
            raise ValueError(
                "Probabilities are empty."
            )

        if np.any(
            (probabilities < 0)
            | (probabilities > 1)
        ):
            raise ValueError(
                "Probabilities must be in [0, 1]."
            )

        return probabilities

    @staticmethod
    def confusion_matrix(
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, int]:

        y_true = np.asarray(y_true).astype(int)
        y_pred = np.asarray(y_pred).astype(int)

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

    def evaluate(
        self,
        y_true: np.ndarray,
        probabilities: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Evaluate abnormality probabilities.

        Args:
            y_true:
                Ground-truth labels:
                0 = normal
                1 = abnormal.

            probabilities:
                Probability of abnormality.
        """

        y_true = self._validate_labels(y_true)
        probabilities = self._validate_probabilities(
            probabilities
        )

        if len(y_true) != len(probabilities):
            raise ValueError(
                "y_true and probabilities must "
                "have the same length."
            )

        y_pred = (
            probabilities >= self.threshold
        ).astype(int)

        cm = self.confusion_matrix(
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

        balanced_accuracy = (
            (recall + specificity) / 2.0
        )

        report: Dict[str, Any] = {
            "task": "binary_abnormality_detection",
            "label_mapping": {
                "0": "normal",
                "1": "abnormal",
            },
            "threshold": self.threshold,
            "n_samples": int(total),
            "positive_samples": int(
                np.sum(y_true == 1)
            ),
            "negative_samples": int(
                np.sum(y_true == 0)
            ),
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall_sensitivity": float(recall),
            "specificity": float(specificity),
            "f1": float(f1),
            "balanced_accuracy": float(
                balanced_accuracy
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

        y_true = self._validate_labels(y_true)
        probabilities = self._validate_probabilities(
            probabilities
        )

        if len(y_true) != len(probabilities):
            raise ValueError(
                "Arrays must have the same length."
            )

        if thresholds is None:
            thresholds = np.linspace(
                0.1,
                0.9,
                17,
            )

        results = []

        for threshold in thresholds:

            predictions = (
                probabilities >= threshold
            ).astype(int)

            cm = self.confusion_matrix(
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
        filename: str = "abnormality_evaluation.json",
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

    abnormality_probability = np.array(
        [
            0.10,
            0.20,
            0.30,
            0.40,
            0.90,
            0.80,
            0.70,
            0.60,
            0.55,
            0.25,
        ]
    )

    evaluator = AbnormalityEvaluator(
        threshold=0.5
    )

    report = evaluator.evaluate(
        y_true,
        abnormality_probability,
    )

    report["threshold_analysis"] = (
        evaluator.threshold_analysis(
            y_true,
            abnormality_probability,
        )
    )

    path = evaluator.save_report(report)

    print("Abnormality evaluation:")

    for key, value in report.items():
        if key != "threshold_analysis":
            print(f"{key}: {value}")

    print(f"\nReport saved to: {path}")


if __name__ == "__main__":
    main()