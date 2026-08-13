"""
Evaluation utilities for pathology classification.

Typical use:
    normal vs BCC vs melanoma

Supports:
- accuracy
- macro precision
- macro recall
- macro F1
- weighted F1
- per-class metrics
- confusion matrix
- ROC-AUC for multiclass probabilities
- balanced accuracy

Expected labels:
    integer class IDs starting from 0.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


class PathologyEvaluator:
    """
    Evaluator for multiclass pathology classification.
    """

    def __init__(
        self,
        class_names: Optional[list[str]] = None,
        output_dir: str = "outputs/reports/pathology",
    ):
        self.class_names = class_names

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _validate_labels(
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:

        y_true = np.asarray(y_true).reshape(-1)
        y_pred = np.asarray(y_pred).reshape(-1)

        if len(y_true) != len(y_pred):
            raise ValueError(
                "y_true and y_pred must have "
                "the same length."
            )

        if len(y_true) == 0:
            raise ValueError(
                "Evaluation arrays are empty."
            )

        return (
            y_true.astype(int),
            y_pred.astype(int),
        )

    def confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        num_classes: int,
    ) -> np.ndarray:

        matrix = np.zeros(
            (num_classes, num_classes),
            dtype=int,
        )

        for true_label, predicted_label in zip(
            y_true,
            y_pred,
        ):

            if not (
                0 <= true_label < num_classes
                and 0 <= predicted_label < num_classes
            ):
                raise ValueError(
                    "Labels are outside the configured "
                    "class range."
                )

            matrix[
                true_label,
                predicted_label,
            ] += 1

        return matrix

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        probabilities: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:

        y_true, y_pred = self._validate_labels(
            y_true,
            y_pred,
        )

        if self.class_names is not None:
            num_classes = len(self.class_names)
        else:
            num_classes = int(
                max(
                    np.max(y_true),
                    np.max(y_pred),
                )
                + 1
            )

        matrix = self.confusion_matrix(
            y_true,
            y_pred,
            num_classes,
        )

        per_class = {}

        precisions = []
        recalls = []
        f1_values = []
        supports = []

        for class_id in range(num_classes):

            tp = matrix[
                class_id,
                class_id,
            ]

            fp = (
                matrix[:, class_id].sum()
                - tp
            )

            fn = (
                matrix[class_id, :].sum()
                - tp
            )

            support = matrix[
                class_id,
                :
            ].sum()

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

            f1 = (
                2 * precision * recall
                / (precision + recall)
                if precision + recall > 0
                else 0.0
            )

            name = (
                self.class_names[class_id]
                if self.class_names is not None
                else str(class_id)
            )

            per_class[name] = {
                "class_id": int(class_id),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "support": int(support),
            }

            precisions.append(precision)
            recalls.append(recall)
            f1_values.append(f1)
            supports.append(support)

        accuracy = float(
            np.mean(y_true == y_pred)
        )

        macro_precision = float(
            np.mean(precisions)
        )

        macro_recall = float(
            np.mean(recalls)
        )

        macro_f1 = float(
            np.mean(f1_values)
        )

        supports_array = np.asarray(
            supports,
            dtype=float,
        )

        if supports_array.sum() > 0:
            weighted_f1 = float(
                np.average(
                    f1_values,
                    weights=supports_array,
                )
            )
        else:
            weighted_f1 = 0.0

        report: Dict[str, Any] = {
            "task": "pathology_classification",
            "n_samples": int(len(y_true)),
            "num_classes": int(num_classes),
            "class_names": self.class_names,
            "accuracy": accuracy,
            "macro_precision": macro_precision,
            "macro_recall": macro_recall,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "balanced_accuracy": macro_recall,
            "per_class": per_class,
            "confusion_matrix": matrix.tolist(),
        }

        if probabilities is not None:

            probabilities = np.asarray(
                probabilities,
                dtype=float,
            )

            if probabilities.ndim != 2:
                raise ValueError(
                    "Multiclass probabilities must "
                    "have shape (N, C)."
                )

            if probabilities.shape[0] != len(
                y_true
            ):
                raise ValueError(
                    "Probability matrix has "
                    "incorrect number of samples."
                )

            try:
                from sklearn.metrics import (
                    roc_auc_score,
                )

                if num_classes == 2:

                    auc = roc_auc_score(
                        y_true,
                        probabilities[:, 1],
                    )

                else:

                    auc = roc_auc_score(
                        y_true,
                        probabilities,
                        multi_class="ovr",
                        average="macro",
                    )

                report["roc_auc_ovr_macro"] = float(
                    auc
                )

            except Exception:
                report["roc_auc_ovr_macro"] = None

        return report

    def save_report(
        self,
        report: Dict[str, Any],
        filename: str = "pathology_evaluation.json",
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

    class_names = [
        "normal",
        "bcc",
        "melanoma",
    ]

    y_true = np.array(
        [
            0, 0, 0,
            1, 1, 1,
            2, 2, 2,
            2, 1,
        ]
    )

    y_pred = np.array(
        [
            0, 0, 1,
            1, 1, 2,
            2, 2, 2,
            1, 1,
        ]
    )

    probabilities = np.array(
        [
            [0.90, 0.08, 0.02],
            [0.80, 0.15, 0.05],
            [0.45, 0.45, 0.10],

            [0.10, 0.80, 0.10],
            [0.05, 0.85, 0.10],
            [0.10, 0.45, 0.45],

            [0.05, 0.10, 0.85],
            [0.05, 0.10, 0.85],
            [0.05, 0.10, 0.85],

            [0.10, 0.75, 0.15],
            [0.10, 0.70, 0.20],
        ]
    )

    evaluator = PathologyEvaluator(
        class_names=class_names
    )

    report = evaluator.evaluate(
        y_true,
        y_pred,
        probabilities,
    )

    path = evaluator.save_report(report)

    print(
        json.dumps(
            report,
            indent=2,
        )
    )

    print(f"\nReport saved to: {path}")


if __name__ == "__main__":
    main()