"""
Evaluation utilities for image/tissue/cell segmentation.

Main metrics:
- Dice coefficient
- IoU
- Precision
- Recall
- Pixel accuracy

The evaluator expects binary masks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np


class SegmentationEvaluator:
    """
    Evaluates predicted segmentation masks against ground truth masks.
    """

    def __init__(self, output_dir: str = "outputs/reports/segmentation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _prepare_masks(
        prediction: np.ndarray,
        target: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:

        prediction = np.asarray(prediction).astype(bool)
        target = np.asarray(target).astype(bool)

        if prediction.shape != target.shape:
            raise ValueError(
                f"Mask shapes do not match: "
                f"{prediction.shape} vs {target.shape}"
            )

        return prediction, target

    @staticmethod
    def dice(
        prediction: np.ndarray,
        target: np.ndarray,
        epsilon: float = 1e-8,
    ) -> float:

        prediction, target = SegmentationEvaluator._prepare_masks(
            prediction,
            target,
        )

        intersection = np.logical_and(
            prediction,
            target,
        ).sum()

        denominator = prediction.sum() + target.sum()

        if denominator == 0:
            return 1.0

        return float(
            (2.0 * intersection + epsilon)
            / (denominator + epsilon)
        )

    @staticmethod
    def iou(
        prediction: np.ndarray,
        target: np.ndarray,
        epsilon: float = 1e-8,
    ) -> float:

        prediction, target = SegmentationEvaluator._prepare_masks(
            prediction,
            target,
        )

        intersection = np.logical_and(
            prediction,
            target,
        ).sum()

        union = np.logical_or(
            prediction,
            target,
        ).sum()

        if union == 0:
            return 1.0

        return float(
            (intersection + epsilon)
            / (union + epsilon)
        )

    @staticmethod
    def confusion(
        prediction: np.ndarray,
        target: np.ndarray,
    ) -> Dict[str, int]:

        prediction, target = SegmentationEvaluator._prepare_masks(
            prediction,
            target,
        )

        tp = int(np.logical_and(prediction, target).sum())
        tn = int(np.logical_and(~prediction, ~target).sum())
        fp = int(np.logical_and(prediction, ~target).sum())
        fn = int(np.logical_and(~prediction, target).sum())

        return {
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
        }

    def evaluate(
        self,
        prediction: np.ndarray,
        target: np.ndarray,
    ) -> Dict[str, Any]:

        prediction, target = self._prepare_masks(
            prediction,
            target,
        )

        cm = self.confusion(prediction, target)

        tp = cm["true_positive"]
        tn = cm["true_negative"]
        fp = cm["false_positive"]
        fn = cm["false_negative"]

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0

        accuracy = (
            (tp + tn) / (tp + tn + fp + fn)
            if (tp + tn + fp + fn)
            else 0.0
        )

        return {
            "task": "binary_segmentation",
            "dice": self.dice(prediction, target),
            "iou": self.iou(prediction, target),
            "precision": float(precision),
            "recall": float(recall),
            "pixel_accuracy": float(accuracy),
            **cm,
        }

    def evaluate_batch(
        self,
        predictions: list[np.ndarray],
        targets: list[np.ndarray],
    ) -> Dict[str, Any]:

        if len(predictions) != len(targets):
            raise ValueError(
                "Predictions and targets must contain "
                "the same number of masks."
            )

        metrics = [
            self.evaluate(pred, target)
            for pred, target in zip(predictions, targets)
        ]

        aggregate: Dict[str, Any] = {
            "task": "binary_segmentation_batch",
            "n_samples": len(metrics),
        }

        for key in [
            "dice",
            "iou",
            "precision",
            "recall",
            "pixel_accuracy",
        ]:
            values = [item[key] for item in metrics]
            aggregate[f"mean_{key}"] = float(np.mean(values))
            aggregate[f"std_{key}"] = float(np.std(values))

        aggregate["samples"] = metrics

        return aggregate

    def save_report(
        self,
        report: Dict[str, Any],
        filename: str = "segmentation_evaluation.json",
    ) -> Path:

        path = self.output_dir / filename

        with path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return path


def main() -> None:

    target = np.zeros((128, 128), dtype=np.uint8)
    prediction = np.zeros((128, 128), dtype=np.uint8)

    target[30:90, 30:90] = 1
    prediction[32:88, 32:88] = 1

    evaluator = SegmentationEvaluator()

    report = evaluator.evaluate(
        prediction,
        target,
    )

    path = evaluator.save_report(report)

    print("Segmentation evaluation:")

    for key, value in report.items():
        print(f"{key}: {value}")

    print(f"\nReport saved to: {path}")


if __name__ == "__main__":
    main()