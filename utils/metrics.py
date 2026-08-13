# utils/metrics.py

from __future__ import annotations

from typing import Optional

import numpy as np


def accuracy(
    y_true,
    y_pred,
) -> float:
    """
    Classification accuracy.
    """

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if y_true.shape != y_pred.shape:
        raise ValueError(
            "y_true and y_pred must have the same shape."
        )

    return float(
        np.mean(y_true == y_pred)
    )


def binary_precision(
    y_true,
    y_pred,
) -> float:
    """
    Binary precision.
    """

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    tp = np.sum(
        (y_true == 1)
        & (y_pred == 1)
    )

    fp = np.sum(
        (y_true == 0)
        & (y_pred == 1)
    )

    denominator = tp + fp

    if denominator == 0:
        return 0.0

    return float(
        tp / denominator
    )


def binary_recall(
    y_true,
    y_pred,
) -> float:
    """
    Binary recall / sensitivity.
    """

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    tp = np.sum(
        (y_true == 1)
        & (y_pred == 1)
    )

    fn = np.sum(
        (y_true == 1)
        & (y_pred == 0)
    )

    denominator = tp + fn

    if denominator == 0:
        return 0.0

    return float(
        tp / denominator
    )


def binary_specificity(
    y_true,
    y_pred,
) -> float:
    """
    Binary specificity.
    """

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    tn = np.sum(
        (y_true == 0)
        & (y_pred == 0)
    )

    fp = np.sum(
        (y_true == 0)
        & (y_pred == 1)
    )

    denominator = tn + fp

    if denominator == 0:
        return 0.0

    return float(
        tn / denominator
    )


def f1_score(
    y_true,
    y_pred,
) -> float:
    """
    Binary F1 score.
    """

    precision = binary_precision(
        y_true,
        y_pred,
    )

    recall = binary_recall(
        y_true,
        y_pred,
    )

    denominator = precision + recall

    if denominator == 0:
        return 0.0

    return float(
        2
        * precision
        * recall
        / denominator
    )


def mean_absolute_error(
    y_true,
    y_pred,
) -> float:
    """
    Mean absolute error.
    """

    y_true = np.asarray(
        y_true,
        dtype=np.float32,
    )

    y_pred = np.asarray(
        y_pred,
        dtype=np.float32,
    )

    return float(
        np.mean(
            np.abs(y_true - y_pred)
        )
    )


def mean_squared_error(
    y_true,
    y_pred,
) -> float:
    """
    Mean squared error.
    """

    y_true = np.asarray(
        y_true,
        dtype=np.float32,
    )

    y_pred = np.asarray(
        y_pred,
        dtype=np.float32,
    )

    return float(
        np.mean(
            (y_true - y_pred) ** 2
        )
    )


def root_mean_squared_error(
    y_true,
    y_pred,
) -> float:
    """
    Root mean squared error.
    """

    return float(
        np.sqrt(
            mean_squared_error(
                y_true,
                y_pred,
            )
        )
    )


def dice_coefficient(
    prediction,
    target,
    smooth: float = 1e-8,
) -> float:
    """
    Dice similarity coefficient for binary masks.
    """

    prediction = np.asarray(
        prediction
    ).astype(bool)

    target = np.asarray(
        target
    ).astype(bool)

    intersection = np.logical_and(
        prediction,
        target,
    ).sum()

    return float(
        (
            2.0 * intersection
            + smooth
        )
        / (
            prediction.sum()
            + target.sum()
            + smooth
        )
    )


def iou_score(
    prediction,
    target,
    smooth: float = 1e-8,
) -> float:
    """
    Intersection over Union.
    """

    prediction = np.asarray(
        prediction
    ).astype(bool)

    target = np.asarray(
        target
    ).astype(bool)

    intersection = np.logical_and(
        prediction,
        target,
    ).sum()

    union = np.logical_or(
        prediction,
        target,
    ).sum()

    return float(
        (intersection + smooth)
        / (union + smooth)
    )


def confusion_matrix_binary(
    y_true,
    y_pred,
) -> dict[str, int]:
    """
    Binary confusion matrix.
    """

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

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


def classification_metrics(
    y_true,
    y_pred,
) -> dict[str, float]:
    """
    Return common binary classification metrics.
    """

    return {
        "accuracy": accuracy(
            y_true,
            y_pred,
        ),
        "precision": binary_precision(
            y_true,
            y_pred,
        ),
        "recall": binary_recall(
            y_true,
            y_pred,
        ),
        "specificity": binary_specificity(
            y_true,
            y_pred,
        ),
        "f1": f1_score(
            y_true,
            y_pred,
        ),
    }