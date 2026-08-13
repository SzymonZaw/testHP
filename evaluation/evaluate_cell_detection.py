"""
Evaluation of cell detection.

This module evaluates predicted cell centers against
ground-truth cell centers.

A prediction is considered correct when it falls within
a configurable Euclidean distance threshold from a ground-truth cell.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np


class CellDetectionEvaluator:
    """
    Evaluates cell-center detection.
    """

    def __init__(
        self,
        distance_threshold: float = 10.0,
        output_dir: str = "outputs/reports/cell_detection",
    ):
        self.distance_threshold = float(distance_threshold)

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _validate_points(
        points: np.ndarray,
    ) -> np.ndarray:

        points = np.asarray(points, dtype=float)

        if points.size == 0:
            return np.empty((0, 2), dtype=float)

        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError(
                "Cell coordinates must have shape (N, 2)."
            )

        return points

    def match_cells(
        self,
        predictions: np.ndarray,
        targets: np.ndarray,
    ) -> tuple[int, int, int]:

        predictions = self._validate_points(predictions)
        targets = self._validate_points(targets)

        if len(predictions) == 0:
            return 0, 0, len(targets)

        if len(targets) == 0:
            return 0, len(predictions), 0

        distances = np.linalg.norm(
            predictions[:, None, :] - targets[None, :, :],
            axis=2,
        )

        matched_predictions = set()
        matched_targets = set()

        pairs = []

        for pred_idx in range(len(predictions)):
            for target_idx in range(len(targets)):
                pairs.append(
                    (
                        distances[pred_idx, target_idx],
                        pred_idx,
                        target_idx,
                    )
                )

        pairs.sort(key=lambda x: x[0])

        for distance, pred_idx, target_idx in pairs:

            if distance > self.distance_threshold:
                break

            if pred_idx in matched_predictions:
                continue

            if target_idx in matched_targets:
                continue

            matched_predictions.add(pred_idx)
            matched_targets.add(target_idx)

        tp = len(matched_predictions)
        fp = len(predictions) - tp
        fn = len(targets) - tp

        return tp, fp, fn

    def evaluate(
        self,
        predictions: np.ndarray,
        targets: np.ndarray,
    ) -> Dict[str, Any]:

        tp, fp, fn = self.match_cells(
            predictions,
            targets,
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
            2 * precision * recall / (precision + recall)
            if precision + recall > 0
            else 0.0
        )

        return {
            "task": "cell_detection",
            "distance_threshold": self.distance_threshold,
            "predicted_cells": int(len(predictions)),
            "ground_truth_cells": int(len(targets)),
            "true_positive": int(tp),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
        }

    def save_report(
        self,
        report: Dict[str, Any],
        filename: str = "cell_detection_evaluation.json",
    ) -> Path:

        path = self.output_dir / filename

        with path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return path


def main() -> None:

    ground_truth = np.array(
        [
            [20, 20],
            [50, 50],
            [80, 80],
            [100, 100],
        ],
        dtype=float,
    )

    predictions = np.array(
        [
            [21, 20],
            [49, 51],
            [81, 79],
            [30, 90],
        ],
        dtype=float,
    )

    evaluator = CellDetectionEvaluator(
        distance_threshold=5.0
    )

    report = evaluator.evaluate(
        predictions,
        ground_truth,
    )

    path = evaluator.save_report(report)

    print("Cell detection evaluation:")

    for key, value in report.items():
        print(f"{key}: {value}")

    print(f"\nReport saved to: {path}")


if __name__ == "__main__":
    main()