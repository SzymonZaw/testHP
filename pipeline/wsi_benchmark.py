"""Benchmark helpers for instance-level nuclei detection and classification.

This module is dataset-agnostic. It expects a prediction instance map and a
reference instance map with integer instance IDs, plus optional per-instance
class labels. It does not download or bundle benchmark datasets.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class DetectionMetrics:
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    mean_iou: float


def _instance_ids(mask: np.ndarray) -> list[int]:
    return [int(x) for x in np.unique(mask) if int(x) != 0]


def _iou(pred: np.ndarray, truth: np.ndarray) -> float:
    inter = np.logical_and(pred, truth).sum()
    union = np.logical_or(pred, truth).sum()
    return float(inter / union) if union else 0.0


def match_instances(
    prediction: np.ndarray,
    reference: np.ndarray,
    iou_threshold: float = 0.5,
) -> tuple[dict[int, int], list[float]]:
    """Greedily match predicted instances to reference instances by IoU."""
    if prediction.shape != reference.shape:
        raise ValueError("prediction and reference must have the same shape")
    if not 0.0 < iou_threshold <= 1.0:
        raise ValueError("iou_threshold must be in (0, 1]")

    pairs: list[tuple[float, int, int]] = []
    pred_ids = _instance_ids(prediction)
    ref_ids = _instance_ids(reference)
    for pid in pred_ids:
        p = prediction == pid
        for rid in ref_ids:
            score = _iou(p, reference == rid)
            if score >= iou_threshold:
                pairs.append((score, pid, rid))

    pairs.sort(reverse=True)
    used_pred: set[int] = set()
    used_ref: set[int] = set()
    matches: dict[int, int] = {}
    ious: list[float] = []
    for score, pid, rid in pairs:
        if pid in used_pred or rid in used_ref:
            continue
        used_pred.add(pid)
        used_ref.add(rid)
        matches[pid] = rid
        ious.append(score)
    return matches, ious


def detection_metrics(
    prediction: np.ndarray,
    reference: np.ndarray,
    iou_threshold: float = 0.5,
) -> DetectionMetrics:
    matches, ious = match_instances(prediction, reference, iou_threshold)
    tp = len(matches)
    fp = len(_instance_ids(prediction)) - tp
    fn = len(_instance_ids(reference)) - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return DetectionMetrics(tp, fp, fn, precision, recall, f1, float(np.mean(ious)) if ious else 0.0)


def classification_metrics(
    matches: Mapping[int, int],
    predicted_labels: Mapping[int, str],
    reference_labels: Mapping[int, str],
) -> dict[str, object]:
    """Return macro-F1-like accuracy summary for matched instances.

    Only matched instances are scored; unmatched nuclei are detection errors,
    not classification labels. Per-class counts are retained for auditability.
    """
    pairs = [(predicted_labels[p], reference_labels[r]) for p, r in matches.items()
             if p in predicted_labels and r in reference_labels]
    correct = sum(a == b for a, b in pairs)
    accuracy = correct / len(pairs) if pairs else 0.0
    labels = sorted(set([a for a, _ in pairs] + [b for _, b in pairs]))
    f1s: list[float] = []
    per_class: dict[str, dict[str, int]] = {}
    for label in labels:
        tp = sum(a == label and b == label for a, b in pairs)
        fp = sum(a == label and b != label for a, b in pairs)
        fn = sum(a != label and b == label for a, b in pairs)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
        per_class[label] = {"tp": tp, "fp": fp, "fn": fn}
    return {
        "n_matched": len(pairs),
        "accuracy": accuracy,
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
        "per_class": per_class,
        "label_counts": dict(Counter(b for _, b in pairs)),
    }
