import numpy as np

from pipeline.wsi_benchmark import classification_metrics, detection_metrics, match_instances


def test_detection_perfect_match():
    truth = np.zeros((10, 10), dtype=np.int32)
    pred = np.zeros_like(truth)
    truth[1:4, 1:4] = 1
    pred[1:4, 1:4] = 7
    metrics = detection_metrics(pred, truth)
    assert metrics.tp == 1
    assert metrics.fp == 0
    assert metrics.fn == 0
    assert metrics.f1 == 1.0
    assert metrics.mean_iou == 1.0


def test_detection_false_positive_and_miss():
    truth = np.zeros((10, 10), dtype=np.int32)
    pred = np.zeros_like(truth)
    truth[1:4, 1:4] = 1
    pred[6:9, 6:9] = 2
    metrics = detection_metrics(pred, truth)
    assert (metrics.tp, metrics.fp, metrics.fn) == (0, 1, 1)


def test_classification_on_matched_instances():
    matches, _ = match_instances(
        np.pad(np.ones((2, 2), dtype=np.int32), ((1, 7), (1, 7))),
        np.pad(np.ones((2, 2), dtype=np.int32), ((1, 7), (1, 7))),
    )
    result = classification_metrics(matches, {1: "epithelial"}, {1: "epithelial"})
    assert result["accuracy"] == 1.0
    assert result["macro_f1"] == 1.0
