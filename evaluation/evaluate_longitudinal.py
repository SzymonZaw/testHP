"""
Evaluation utilities for longitudinal predictions.

Designed for:
    T0 -> T1 -> T2 -> T3

Supports:
- per-timepoint MAE
- RMSE
- bias
- temporal consistency
- direction/trend agreement
- mean absolute change error
- longitudinal report generation

The evaluator is intentionally generic and can be used for:
- biological age
- risk score
- tissue state
- pathology score
- other longitudinal continuous predictions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


class LongitudinalEvaluator:
    """
    Evaluates predictions across multiple timepoints.
    """

    def __init__(
        self,
        timepoints: Optional[list[str]] = None,
        output_dir: str = "outputs/reports/longitudinal",
    ):
        self.timepoints = timepoints or [
            "T0",
            "T1",
            "T2",
            "T3",
        ]

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _validate_matrix(
        values: np.ndarray,
    ) -> np.ndarray:

        values = np.asarray(
            values,
            dtype=float,
        )

        if values.ndim != 2:
            raise ValueError(
                "Longitudinal values must have "
                "shape (N, T)."
            )

        if values.shape[0] == 0:
            raise ValueError(
                "Longitudinal dataset is empty."
            )

        if values.shape[1] < 2:
            raise ValueError(
                "At least two timepoints are required."
            )

        return values

    @staticmethod
    def _regression_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, Optional[float]]:

        error = y_pred - y_true

        mae = float(
            np.mean(
                np.abs(error)
            )
        )

        rmse = float(
            np.sqrt(
                np.mean(
                    error ** 2
                )
            )
        )

        bias = float(
            np.mean(error)
        )

        ss_res = float(
            np.sum(error ** 2)
        )

        ss_tot = float(
            np.sum(
                (
                    y_true
                    - np.mean(y_true)
                ) ** 2
            )
        )

        if ss_tot > 0:
            r2 = float(
                1.0
                - ss_res / ss_tot
            )
        else:
            r2 = None

        return {
            "mae": mae,
            "rmse": rmse,
            "bias": bias,
            "r2": r2,
        }

    def evaluate_per_timepoint(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, Dict[str, Any]]:

        y_true = self._validate_matrix(y_true)
        y_pred = self._validate_matrix(y_pred)

        if y_true.shape != y_pred.shape:
            raise ValueError(
                "Ground truth and predictions "
                "must have identical shapes."
            )

        n_timepoints = y_true.shape[1]

        if n_timepoints != len(self.timepoints):
            names = [
                f"T{i}"
                for i in range(n_timepoints)
            ]
        else:
            names = self.timepoints

        result = {}

        for index, name in enumerate(names):

            result[name] = self._regression_metrics(
                y_true[:, index],
                y_pred[:, index],
            )

        return result

    def evaluate_temporal_changes(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Evaluate changes between consecutive timepoints.

        Example:

            T0 -> T1
            T1 -> T2
            T2 -> T3
        """

        y_true = self._validate_matrix(y_true)
        y_pred = self._validate_matrix(y_pred)

        if y_true.shape != y_pred.shape:
            raise ValueError(
                "Ground truth and predictions "
                "must have identical shapes."
            )

        true_changes = np.diff(
            y_true,
            axis=1,
        )

        predicted_changes = np.diff(
            y_pred,
            axis=1,
        )

        change_error = (
            predicted_changes
            - true_changes
        )

        mae = float(
            np.mean(
                np.abs(change_error)
            )
        )

        rmse = float(
            np.sqrt(
                np.mean(
                    change_error ** 2
                )
            )
        )

        true_direction = np.sign(
            true_changes
        )

        predicted_direction = np.sign(
            predicted_changes
        )

        direction_accuracy = float(
            np.mean(
                true_direction
                == predicted_direction
            )
        )

        interval_results = {}

        for index in range(
            true_changes.shape[1]
        ):

            if index + 1 < len(
                self.timepoints
            ):
                name = (
                    f"{self.timepoints[index]}"
                    f"->{self.timepoints[index + 1]}"
                )
            else:
                name = f"T{index}->T{index + 1}"

            interval_error = (
                change_error[:, index]
            )

            interval_results[name] = {
                "mae": float(
                    np.mean(
                        np.abs(
                            interval_error
                        )
                    )
                ),
                "rmse": float(
                    np.sqrt(
                        np.mean(
                            interval_error ** 2
                        )
                    )
                ),
                "mean_change_error": float(
                    np.mean(
                        interval_error
                    )
                ),
                "direction_accuracy": float(
                    np.mean(
                        true_direction[:, index]
                        == predicted_direction[:, index]
                    )
                ),
            }

        return {
            "global_change_mae": mae,
            "global_change_rmse": rmse,
            "global_direction_accuracy": (
                direction_accuracy
            ),
            "intervals": interval_results,
        }

    def evaluate_patient_trajectories(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Evaluate each individual longitudinal trajectory.
        """

        y_true = self._validate_matrix(y_true)
        y_pred = self._validate_matrix(y_pred)

        if y_true.shape != y_pred.shape:
            raise ValueError(
                "Ground truth and predictions "
                "must have identical shapes."
            )

        patients = []

        for patient_index in range(
            y_true.shape[0]
        ):

            true = y_true[patient_index]
            pred = y_pred[patient_index]

            error = pred - true

            patient_report = {
                "patient_index": int(
                    patient_index
                ),
                "mae": float(
                    np.mean(
                        np.abs(error)
                    )
                ),
                "rmse": float(
                    np.sqrt(
                        np.mean(
                            error ** 2
                        )
                    )
                ),
                "bias": float(
                    np.mean(error)
                ),
                "true_trajectory": (
                    true.tolist()
                ),
                "predicted_trajectory": (
                    pred.tolist()
                ),
            }

            patients.append(
                patient_report
            )

        return {
            "n_patients": len(patients),
            "patients": patients,
        }

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Dict[str, Any]:

        y_true = self._validate_matrix(y_true)
        y_pred = self._validate_matrix(y_pred)

        if y_true.shape != y_pred.shape:
            raise ValueError(
                "Ground truth and predictions "
                "must have identical shapes."
            )

        report = {
            "task": "longitudinal_evaluation",
            "n_patients": int(
                y_true.shape[0]
            ),
            "n_timepoints": int(
                y_true.shape[1]
            ),
            "timepoints": (
                self.timepoints
                if len(self.timepoints)
                == y_true.shape[1]
                else [
                    f"T{i}"
                    for i in range(
                        y_true.shape[1]
                    )
                ]
            ),
            "per_timepoint": (
                self.evaluate_per_timepoint(
                    y_true,
                    y_pred,
                )
            ),
            "temporal_changes": (
                self.evaluate_temporal_changes(
                    y_true,
                    y_pred,
                )
            ),
        }

        return report

    def save_report(
        self,
        report: Dict[str, Any],
        filename: str = "longitudinal_evaluation.json",
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

    evaluator = LongitudinalEvaluator(
        timepoints=[
            "T0",
            "T1",
            "T2",
            "T3",
        ]
    )

    # Rows = patients
    # Columns = T0, T1, T2, T3

    y_true = np.array(
        [
            [40.0, 42.0, 44.0, 46.0],
            [35.0, 36.0, 38.0, 40.0],
            [50.0, 52.0, 55.0, 57.0],
            [60.0, 61.0, 63.0, 66.0],
        ]
    )

    y_pred = np.array(
        [
            [41.0, 42.5, 43.5, 46.5],
            [34.0, 37.0, 38.5, 39.0],
            [49.0, 51.5, 55.5, 58.0],
            [61.0, 60.5, 63.5, 65.0],
        ]
    )

    report = evaluator.evaluate(
        y_true,
        y_pred,
    )

    trajectory_report = (
        evaluator.evaluate_patient_trajectories(
            y_true,
            y_pred,
        )
    )

    report["patient_trajectories"] = (
        trajectory_report
    )

    path = evaluator.save_report(report)

    print("Longitudinal evaluation:")

    print(
        json.dumps(
            report,
            indent=2,
        )
    )

    print(
        f"\nReport saved to: {path}"
    )


if __name__ == "__main__":
    main()