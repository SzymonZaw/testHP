"""
Evaluation utilities for RNA / single-cell analysis.

Supports:
- classification metrics,
- clustering metrics,
- optional Scanpy-based evaluation,
- expression matrix sanity checks.

This module intentionally does not assume one specific RNA dataset.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


class RNAEvaluator:
    """
    Evaluator for RNA analysis pipelines.
    """

    def __init__(
        self,
        output_dir: str = "outputs/reports/rna",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def classification_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, Any]:

        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        if len(y_true) != len(y_pred):
            raise ValueError(
                "y_true and y_pred must have equal length."
            )

        labels = np.unique(
            np.concatenate([y_true, y_pred])
        )

        per_class = {}

        for label in labels:

            tp = np.sum(
                (y_true == label) &
                (y_pred == label)
            )

            fp = np.sum(
                (y_true != label) &
                (y_pred == label)
            )

            fn = np.sum(
                (y_true == label) &
                (y_pred != label)
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

            f1 = (
                2 * precision * recall
                / (precision + recall)
                if precision + recall > 0
                else 0.0
            )

            per_class[str(label)] = {
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "support": int(np.sum(y_true == label)),
            }

        accuracy = float(
            np.mean(y_true == y_pred)
        )

        macro_f1 = float(
            np.mean(
                [
                    item["f1"]
                    for item in per_class.values()
                ]
            )
        )

        return {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "classes": per_class,
            "n_samples": int(len(y_true)),
        }

    @staticmethod
    def clustering_metrics(
        labels_true: np.ndarray,
        labels_pred: np.ndarray,
    ) -> Dict[str, Any]:

        labels_true = np.asarray(labels_true)
        labels_pred = np.asarray(labels_pred)

        if len(labels_true) != len(labels_pred):
            raise ValueError(
                "Clustering label arrays must have equal length."
            )

        try:
            from sklearn.metrics import (
                adjusted_rand_score,
                normalized_mutual_info_score,
            )
        except ImportError as exc:
            raise ImportError(
                "scikit-learn is required for clustering metrics."
            ) from exc

        ari = adjusted_rand_score(
            labels_true,
            labels_pred,
        )

        nmi = normalized_mutual_info_score(
            labels_true,
            labels_pred,
        )

        return {
            "adjusted_rand_index": float(ari),
            "normalized_mutual_information": float(nmi),
            "n_samples": int(len(labels_true)),
        }

    @staticmethod
    def expression_matrix_quality(
        expression: np.ndarray,
    ) -> Dict[str, Any]:

        expression = np.asarray(
            expression,
            dtype=float,
        )

        if expression.ndim != 2:
            raise ValueError(
                "Expression matrix must be 2-dimensional."
            )

        finite_ratio = np.mean(
            np.isfinite(expression)
        )

        zero_ratio = np.mean(
            expression == 0
        )

        return {
            "n_cells": int(expression.shape[0]),
            "n_genes": int(expression.shape[1]),
            "finite_ratio": float(finite_ratio),
            "zero_ratio": float(zero_ratio),
            "mean_expression": float(
                np.nanmean(expression)
            ),
            "median_expression": float(
                np.nanmedian(expression)
            ),
        }

    def evaluate(
        self,
        expression: Optional[np.ndarray] = None,
        y_true: Optional[np.ndarray] = None,
        y_pred: Optional[np.ndarray] = None,
        cluster_true: Optional[np.ndarray] = None,
        cluster_pred: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:

        report: Dict[str, Any] = {
            "task": "rna_evaluation"
        }

        if expression is not None:
            report["expression_quality"] = (
                self.expression_matrix_quality(
                    expression
                )
            )

        if y_true is not None and y_pred is not None:
            report["classification"] = (
                self.classification_metrics(
                    y_true,
                    y_pred,
                )
            )

        if (
            cluster_true is not None
            and cluster_pred is not None
        ):
            report["clustering"] = (
                self.clustering_metrics(
                    cluster_true,
                    cluster_pred,
                )
            )

        return report

    def save_report(
        self,
        report: Dict[str, Any],
        filename: str = "rna_evaluation.json",
    ) -> Path:

        path = self.output_dir / filename

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                report,
                f,
                indent=2,
            )

        return path


def main() -> None:

    rng = np.random.default_rng(42)

    expression = rng.poisson(
        lam=2.0,
        size=(100, 500),
    )

    y_true = np.array(
        ["keratinocyte"] * 50
        + ["fibroblast"] * 50
    )

    y_pred = np.array(
        ["keratinocyte"] * 45
        + ["fibroblast"] * 5
        + ["keratinocyte"] * 8
        + ["fibroblast"] * 42
    )

    evaluator = RNAEvaluator()

    report = evaluator.evaluate(
        expression=expression,
        y_true=y_true,
        y_pred=y_pred,
    )

    path = evaluator.save_report(report)

    print(json.dumps(
        report,
        indent=2,
        default=str,
    ))

    print(f"\nReport saved to: {path}")


if __name__ == "__main__":
    main()